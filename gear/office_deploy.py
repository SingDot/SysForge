import subprocess
import os
import sys
import time
import winreg

CREATE_NO_WINDOW = 0x08000000

def obter_caminho_base():
    """
    Retorna o caminho do diretório base do aplicativo.
    Funciona tanto ao rodar via script (.py) quanto via executável (PyInstaller).
    """
    if getattr(sys, 'frozen', False):
        # Quando compilado com PyInstaller --add-data, os arquivos ficam na pasta temporária _MEIPASS
        return sys._MEIPASS
    else:
        # Se rodando via script .py, usa o caminho deste arquivo subindo até a raiz SysForge
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _verificar_office_instalado():
    """Verifica se o Office foi instalado com sucesso checando o registro C2R."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Office\ClickToRun\Configuration",
            0, winreg.KEY_READ
        )
        val, _ = winreg.QueryValueEx(key, "ProductReleaseIds")
        winreg.CloseKey(key)
        return bool(val and val.strip())
    except OSError:
        return False


def install_and_activate_office(status_callback=None, progress_callback=None):
    """
    Instala e ativa o Office LTSC 2021.
    
    Fases de progresso:
      0%  → 10%  : Preparação (validação de arquivos, config temporário)
      10% → 70%  : Instalação (setup.exe /configure — download + install)
      70% → 80%  : Verificação pós-instalação
      80% → 100% : Ativação (MAS /Ohook)
    """
    def _progress(pct):
        if progress_callback:
            progress_callback(pct)

    def _status(msg):
        if status_callback:
            status_callback(msg)

    base_dir = obter_caminho_base()
    office_dir = os.path.join(base_dir, "OfficeInstall")
    setup_exe = os.path.join(office_dir, "setup.exe")
    config_xml = os.path.join(office_dir, "config.xml")

    # ─── FASE 1: Preparação (0% → 10%) ─────────────────────
    _status("⏳ [1/4] Validando arquivos do Office Deployment Tool...")
    _progress(0.02)

    if not os.path.exists(setup_exe):
        _status(f"❌ Falta setup.exe em: {setup_exe}")
        return
    if not os.path.exists(config_xml):
        _status(f"❌ Falta config.xml em: {config_xml}")
        return

    _progress(0.05)
    _status("⏳ [1/4] Preparando configuração de instalação...")

    # Gera config temporário com Level="Full" e FORCEAPPSHUTDOWN="TRUE"
    import tempfile
    try:
        with open(config_xml, "r", encoding="utf-8") as f:
            xml_data = f.read()
    except Exception as e:
        _status(f"❌ Erro ao ler config.xml: {e}")
        return

    # Garantir que o instalador mostre progresso visual
    xml_data = xml_data.replace('Level="None"', 'Level="Full"')
    # Forçar fechamento de apps do Office que possam estar abertos
    xml_data = xml_data.replace('FORCEAPPSHUTDOWN" Value="FALSE"', 'FORCEAPPSHUTDOWN" Value="TRUE"')

    run_config = os.path.join(tempfile.gettempdir(), "sysforge_office_config.xml")
    try:
        with open(run_config, "w", encoding="utf-8") as f:
            f.write(xml_data)
    except Exception as e:
        _status(f"❌ Erro ao criar config temporário: {e}")
        return

    _progress(0.10)

    # ─── FASE 2: Instalação (10% → 70%) ────────────────────
    _status("🚀 [2/4] Executando instalador do Office — a janela do instalador aparecerá em breve...")

    try:
        # NÃO usar CREATE_NO_WINDOW aqui — o ODT precisa criar janelas filhas
        # para a interface de download e instalação do Office
        p = subprocess.Popen(
            [setup_exe, "/configure", run_config],
            cwd=office_dir
        )

        # Monitorar o processo com feedback de progresso
        # O ODT demora tipicamente 5-30 minutos dependendo da conexão
        start_time = time.time()
        timeout_seconds = 3600  # 1 hora máxima

        while p.poll() is None:
            elapsed = time.time() - start_time

            if elapsed > timeout_seconds:
                p.kill()
                _status("❌ Timeout: instalação excedeu 1 hora. Verifique sua conexão de internet.")
                _cleanup_temp(run_config)
                return

            # Progresso simulado linear durante a instalação (10% → 70%)
            # O ODT não expõe progresso via stdout, mas mostra sua própria janela
            simulated_pct = 0.10 + min(0.60, (elapsed / 1800) * 0.60)  # 30min = 70%
            _progress(simulated_pct)

            # Atualiza mensagem a cada 30 segundos
            mins = int(elapsed // 60)
            secs = int(elapsed % 60)
            if mins > 0:
                _status(f"🚀 [2/4] Instalando Office... ({mins}m{secs:02d}s decorridos)")
            else:
                _status(f"🚀 [2/4] Instalando Office... ({secs}s decorridos)")

            time.sleep(2)

        if p.returncode != 0:
            _status(f"❌ Instalação do Office falhou (Código de saída: {p.returncode}).")
            _cleanup_temp(run_config)
            return

    except Exception as e:
        _status(f"❌ Falha ao executar o instalador: {str(e)}")
        _cleanup_temp(run_config)
        return

    _cleanup_temp(run_config)
    _progress(0.70)

    # ─── FASE 3: Verificação Pós-Instalação (70% → 80%) ───
    _status("🔍 [3/4] Verificando instalação no registro do Windows...")
    time.sleep(2)  # Aguarda registro ser escrito

    if _verificar_office_instalado():
        _status("✅ [3/4] Office detectado no sistema — instalação confirmada!")
    else:
        _status("⚠️ [3/4] Office não detectado no registro — a instalação pode ter falhado parcialmente.")
        # Não retorna — tenta ativar de qualquer forma (pode ser um atraso no registro)

    _progress(0.80)

    # ─── FASE 4: Ativação (80% → 100%) ─────────────────────
    _status("🔑 [4/4] Ativando Office LTSC via MAS (pode demorar 1-2 minutos)...")
    _progress(0.85)

    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0  # SW_HIDE

        cmd = [
            "powershell.exe", "-WindowStyle", "Hidden",
            "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-Command",
            "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; "
            "& ([ScriptBlock]::Create((irm https://get.activated.win))) /Ohook /S"
        ]

        result = subprocess.run(
            cmd,
            creationflags=CREATE_NO_WINDOW,
            startupinfo=startupinfo,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutos máximo
            encoding="utf-8",
            errors="replace"
        )

        _progress(0.95)

        if result.returncode == 0:
            _status("✅ Office instalado e ativado com sucesso!")
        else:
            # Captura detalhes do erro para feedback
            err_detail = (result.stderr or result.stdout or "").strip()
            err_snippet = err_detail[:200] if err_detail else "Sem detalhes"
            _status(f"⚠️ Ativação retornou código {result.returncode}. Detalhes: {err_snippet}")

    except subprocess.TimeoutExpired:
        _status("⚠️ Ativação excedeu 5 minutos — tente ativar manualmente mais tarde.")
    except Exception as e:
        _status(f"❌ Erro ao ativar o Office: {str(e)}")

    _progress(1.0)


def _cleanup_temp(path):
    """Remove arquivo de config temporário."""
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass

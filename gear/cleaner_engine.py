import os
import stat
import shutil
import subprocess
import psutil

CREATE_NO_WINDOW = 0x08000000

PROCESSOS_NAVEGADORES = {
    "chrome.exe": "Google Chrome",
    "msedge.exe": "Microsoft Edge",
    "brave.exe": "Brave Browser",
    "firefox.exe": "Mozilla Firefox",
    "opera.exe": "Opera GX"
}

def verificar_navegadores_abertos():
    abertos = set()
    for proc in psutil.process_iter(['name']):
        try:
            name = proc.info.get('name')
            if name and name.lower() in PROCESSOS_NAVEGADORES:
                abertos.add(PROCESSOS_NAVEGADORES[name.lower()])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return list(abertos)

def encerrar_navegadores(navegadores_para_matar):
    nomes_to_exe = {v: k for k, v in PROCESSOS_NAVEGADORES.items()}
    exes_to_kill = [nomes_to_exe[n] for n in navegadores_para_matar if n in nomes_to_exe]
    
    for proc in psutil.process_iter(['name']):
        try:
            name = proc.info.get('name')
            if name and name.lower() in exes_to_kill:
                proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

TEMPLATE_ALVOS = {
    "Google Chrome": {
        "_base_path": r"%LocalAppData%\Google\Chrome",
        "Cache da internet": {"tipo": "pasta", "caminho": r"%LocalAppData%\Google\Chrome\User Data\Default\Cache"},
        "Histórico da internet": {"tipo": "arquivo", "caminho": r"%LocalAppData%\Google\Chrome\User Data\Default\History"},
        "Cookies": {"tipo": "arquivo", "caminho": r"%LocalAppData%\Google\Chrome\User Data\Default\Network\Cookies"},
        "Senhas salvas": {"tipo": "arquivo", "caminho": r"%LocalAppData%\Google\Chrome\User Data\Default\Login Data"},
        "Sessão": {"tipo": "pasta", "caminho": r"%LocalAppData%\Google\Chrome\User Data\Default\Sessions"}
    },
    "Microsoft Edge": {
        "_base_path": r"%LocalAppData%\Microsoft\Edge",
        "Cache da internet": {"tipo": "pasta", "caminho": r"%LocalAppData%\Microsoft\Edge\User Data\Default\Cache"},
        "Histórico da internet": {"tipo": "arquivo", "caminho": r"%LocalAppData%\Microsoft\Edge\User Data\Default\History"},
        "Cookies": {"tipo": "arquivo", "caminho": r"%LocalAppData%\Microsoft\Edge\User Data\Default\Network\Cookies"},
        "Senhas salvas": {"tipo": "arquivo", "caminho": r"%LocalAppData%\Microsoft\Edge\User Data\Default\Login Data"},
        "Sessão": {"tipo": "pasta", "caminho": r"%LocalAppData%\Microsoft\Edge\User Data\Default\Sessions"}
    },
    "Brave Browser": {
        "_base_path": r"%LocalAppData%\BraveSoftware\Brave-Browser",
        "Cache da internet": {"tipo": "pasta", "caminho": r"%LocalAppData%\BraveSoftware\Brave-Browser\User Data\Default\Cache"},
        "Histórico da internet": {"tipo": "arquivo", "caminho": r"%LocalAppData%\BraveSoftware\Brave-Browser\User Data\Default\History"},
        "Cookies": {"tipo": "arquivo", "caminho": r"%LocalAppData%\BraveSoftware\Brave-Browser\User Data\Default\Network\Cookies"},
        "Senhas salvas": {"tipo": "arquivo", "caminho": r"%LocalAppData%\BraveSoftware\Brave-Browser\User Data\Default\Login Data"},
        "Sessão": {"tipo": "pasta", "caminho": r"%LocalAppData%\BraveSoftware\Brave-Browser\User Data\Default\Sessions"}
    },
    "Opera GX": {
        "_base_path": r"%AppData%\Opera Software\Opera GX Stable",
        "Cache da internet": {"tipo": "pasta", "caminho": r"%LocalAppData%\Opera Software\Opera GX Stable\Cache"},
        "Histórico da internet": {"tipo": "arquivo", "caminho": r"%AppData%\Opera Software\Opera GX Stable\History"},
        "Cookies": {"tipo": "arquivo", "caminho": r"%AppData%\Opera Software\Opera GX Stable\Cookies"},
        "Senhas salvas": {"tipo": "arquivo", "caminho": r"%AppData%\Opera Software\Opera GX Stable\Login Data"},
        "Sessão": {"tipo": "pasta", "caminho": r"%AppData%\Opera Software\Opera GX Stable\Sessions"}
    },
    "Mozilla Firefox": {
        "_base_path": r"%AppData%\Mozilla\Firefox",
        "Cache da internet": {"tipo": "pasta", "caminho": r"%LocalAppData%\Mozilla\Firefox\Profiles"},
        "Cookies e Dados": {"tipo": "pasta", "caminho": r"%AppData%\Mozilla\Firefox\Profiles"}
    },
    "Discord": {
        "_base_path": r"%AppData%\discord",
        "Cache da internet": {"tipo": "pasta", "caminho": r"%AppData%\discord\Cache"},
        "Code Cache": {"tipo": "pasta", "caminho": r"%AppData%\discord\Code Cache"},
        "GPU Cache": {"tipo": "pasta", "caminho": r"%AppData%\discord\GPUCache"}
    },
    "Sistema": {
        "Arquivos temporários": {"tipo": "pasta", "caminho": r"%TEMP%"},
        "Temp do Windows": {"tipo": "pasta", "caminho": r"C:\Windows\Temp"},
        "Prefetch": {"tipo": "pasta", "caminho": r"C:\Windows\Prefetch"},
        "Despejos de memória": {"tipo": "arquivo", "caminho": r"%SystemRoot%\MEMORY.DMP"},
        "Cache DNS": {"tipo": "comando", "exec": "ipconfig /flushdns"},
        "Esvaziar lixeira": {"tipo": "comando", "exec": r"rd /s /q %systemdrive%\$Recycle.bin"},
        "Windows Update": {"tipo": "pasta", "caminho": r"C:\Windows\SoftwareDistribution\Download"},
        "Relatórios de Erro (Archive)": {"tipo": "pasta", "caminho": r"C:\ProgramData\Microsoft\Windows\WER\ReportArchive"},
        "Relatórios de Erro (Queue)": {"tipo": "pasta", "caminho": r"C:\ProgramData\Microsoft\Windows\WER\ReportQueue"},
        "Otimização de Entrega": {"tipo": "pasta", "caminho": r"C:\Windows\ServiceProfiles\NetworkService\AppData\Local\Microsoft\Windows\DeliveryOptimization\Cache"},
        "Downloads Nativos": {"tipo": "pasta", "caminho": r"%USERPROFILE%\Downloads"}
    },
    "Utilitários": {
        "Windows Defender Scans": {"tipo": "pasta", "caminho": r"C:\ProgramData\Microsoft\Windows Defender\Scans\History\Store"}
    }
}

def obter_alvos_ativos():
    alvos_ativos = {}
    for categoria, itens in TEMPLATE_ALVOS.items():
        if categoria.lower() in ("sistema", "utilitários", "windows"):
            alvos_ativos[categoria] = {}
            for k, v in itens.items():
                if k != "_base_path":
                    v_copy = dict(v)
                    v_copy["_categoria"] = categoria
                    v_copy["_nome"] = k
                    alvos_ativos[categoria][k] = v_copy
            continue
            
        base_path = itens.get("_base_path")
        if base_path:
            expanded_base = os.path.expandvars(base_path)
            if not os.path.exists(expanded_base):
                continue
                
        alvos_ativos[categoria] = {}
        for k, v in itens.items():
            if k != "_base_path":
                v_copy = dict(v)
                v_copy["_categoria"] = categoria
                v_copy["_nome"] = k
                alvos_ativos[categoria][k] = v_copy
        
    return alvos_ativos

def calcular_lixo(alvos_selecionados):
    total_bytes = 0
    log_path = "sysforge_clean_audit.log"
    
    with open(log_path, "w", encoding="utf-8") as f_log:
        f_log.write("=== SYSFORGE AUDITORIA DE LIMPEZA ===\n")
        
        for alvo in alvos_selecionados:
            tipo = alvo.get("tipo")
            cat = alvo.get("_categoria", "UNKNOWN")
            nome = alvo.get("_nome", "UNKNOWN")
            
            if tipo in ("pasta", "arquivo"):
                path = os.path.expandvars(alvo["caminho"])
                if os.path.exists(path):
                    if os.path.isfile(path):
                        try:
                            size = os.path.getsize(path)
                            total_bytes += size
                            f_log.write(f"[{cat.upper()} - {nome.upper()}] {path} -> {size / (1024*1024):.2f} MB\n")
                        except (PermissionError, OSError):
                            f_log.write(f"[IGNORADO - EM USO / NEGADO] {path}\n")
                    elif os.path.isdir(path):
                        for root, dirs, files in os.walk(path):
                            for file in files:
                                fp = os.path.join(root, file)
                                try:
                                    size = os.path.getsize(fp)
                                    total_bytes += size
                                    f_log.write(f"[{cat.upper()} - {nome.upper()}] {fp} -> {size / (1024*1024):.2f} MB\n")
                                except (PermissionError, OSError):
                                    f_log.write(f"[IGNORADO - EM USO / NEGADO] {fp}\n")
    return total_bytes

def _remover_arquivo(fp):
    """Remove um arquivo contornando travas simples. Retorna bytes liberados (0 se falhar)."""
    try:
        size = os.path.getsize(fp)
    except OSError:
        size = 0
    try:
        os.chmod(fp, stat.S_IWRITE)
    except Exception:
        pass
    try:
        os.remove(fp)
        return size
    except Exception:
        subprocess.run(["cmd.exe", "/c", "del", "/f", "/q", fp],
                       creationflags=CREATE_NO_WINDOW, check=False)
        return size if not os.path.exists(fp) else 0


def executar_limpeza(alvos_selecionados, log_callback=None):
    """Executa a limpeza dos alvos. Retorna (bytes_liberados, itens_removidos)."""
    total_bytes = 0
    total_itens = 0

    for alvo in alvos_selecionados:
        tipo = alvo.get("tipo")
        nome = alvo.get("_nome", "item")

        if tipo == "comando":
            cmd = alvo["exec"]
            if log_callback:
                log_callback(f"⚙️ {nome}...")
            try:
                subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, creationflags=CREATE_NO_WINDOW)
            except Exception:
                pass
            continue

        path = os.path.expandvars(alvo["caminho"])
        if not os.path.exists(path):
            continue

        if log_callback:
            log_callback(f"🧹 Limpando {nome}...")

        if os.path.isfile(path):
            freed = _remover_arquivo(path)
            if freed:
                total_bytes += freed
                total_itens += 1
        elif os.path.isdir(path):
            for root, dirs, files in os.walk(path, topdown=False):
                for f in files:
                    fp = os.path.join(root, f)
                    if os.path.basename(fp).startswith("_MEI"):
                        continue
                    freed = _remover_arquivo(fp)
                    if freed:
                        total_bytes += freed
                        total_itens += 1
                for d in dirs:
                    dp = os.path.join(root, d)
                    try:
                        os.rmdir(dp)
                    except Exception:
                        pass

    if log_callback:
        mb = total_bytes / (1024 * 1024)
        log_callback(f"✅ Limpeza concluída: {total_itens} itens, {mb:.2f} MB liberados.")
    return total_bytes, total_itens

import subprocess
import os
import shutil
import glob

CREATE_NO_WINDOW = 0x08000000

SOFTWARE_DICT = {
    "Navegadores": {
        "Google Chrome": "Google.Chrome",
        "Opera": "Opera.Opera",
        "Opera GX": "Opera.OperaGX",
        "Brave": "Brave.Brave"
    },
    "Comunicação": {
        "WhatsApp": "9NKSQGP7F2NH",
        "Telegram": "Telegram.TelegramDesktop",
        "Discord": "Discord.Discord",
        "Zoom": "Zoom.Zoom"
    },
    "Utilitários": {
        "WinRAR": "RARLab.WinRAR",
        "AnyDesk": "AnyDesk.AnyDesk",
        "PowerToys": "Microsoft.PowerToys",
        "Notepad++": "Notepad++.Notepad++",
        "qBittorrent": "qBittorrent.qBittorrent"
    },
    "Desenvolvimento": {
        "Visual Studio Code": "Microsoft.VisualStudioCode",
        "Node.js": "OpenJS.NodeJS",
        "Python 3.12": "Python.Python.3.12",
        "Git": "Git.Git",
        "Docker Desktop": "Docker.DockerDesktop",
        "Postman": "Postman.Postman",
        "Insomnia": "Insomnia.Insomnia",
        "Android Studio": "Google.AndroidStudio",
        "IntelliJ IDEA (Community)": "JetBrains.IntelliJIDEA.Community",
        "Eclipse IDE": "EclipseFoundation.Eclipse.Java",
        "Sublime Text": "SublimeHQ.SublimeText.4",
        "Wireshark": "WiresharkFoundation.Wireshark",
        "VirtualBox": "Oracle.VirtualBox",
        "XAMPP": "ApacheFriends.Xampp.8.2"
    },
    "Bancos de Dados": {
        "DBeaver": "DBeaver.DBeaver.Community",
        "MySQL Server": "Oracle.MySQL",
        "PostgreSQL": "PostgreSQL.PostgreSQL.17",
        "pgAdmin": "PostgreSQL.pgAdmin",
        "SQL Server 2022 Express": "Microsoft.SQLServer.2022.Express",
        "MongoDB Server": "MongoDB.Server",
        "RedisInsight (GUI)": "RedisInsight.RedisInsight"
    },
    "Java / Runtime": {
        "Java JRE 21 (Uso Geral)": "EclipseAdoptium.Temurin.21.JRE",
        "Java JDK 21 (Desenvolvimento)": "EclipseAdoptium.Temurin.21.JDK",
        "Java JRE 8 (Legado)": "EclipseAdoptium.Temurin.8.JRE",
    },
    "Design / Mídia": {
        "K-Lite Codec Pack": "CodecGuide.K-LiteCodecPack.Standard",
        "VLC": "VideoLAN.VLC",
        "OBS Studio": "OBSProject.OBSStudio",
        "Figma": "Figma.Figma",
        "ShareX": "ShareX.ShareX"
    }
}

# Perfis de implantação pré-definidos
PROFILES = {
    "🏢 PC Escritório": [
        "Google.Chrome", "9NKSQGP7F2NH", "RARLab.WinRAR",
        "AnyDesk.AnyDesk", "VideoLAN.VLC",
        "CodecGuide.K-LiteCodecPack.Standard"
    ],
    "🎮 PC Gamer": [
        "Google.Chrome", "Discord.Discord", "Opera.OperaGX",
        "RARLab.WinRAR", "VideoLAN.VLC", "OBSProject.OBSStudio",
        "qBittorrent.qBittorrent", "ShareX.ShareX",
        "CodecGuide.K-LiteCodecPack.Standard"
    ],
    "💻 PC Dev": [
        "Google.Chrome", "Microsoft.VisualStudioCode", "OpenJS.NodeJS",
        "Python.Python.3.12", "Git.Git", "Docker.DockerDesktop",
        "DBeaver.DBeaver.Community", "Postman.Postman", "Discord.Discord",
        "Notepad++.Notepad++", "RARLab.WinRAR", "ShareX.ShareX",
        "EclipseAdoptium.Temurin.21.JDK",
    ],
}

def _friendly_name(winget_id):
    for cat in SOFTWARE_DICT.values():
        for name, wid in cat.items():
            if wid == winget_id:
                return name
    return winget_id


def _find_winget():
    """Localiza o winget.exe de forma confiável.

    Quando o app roda elevado (--uac-admin), o alias em WindowsApps costuma
    sumir do PATH, fazendo a chamada 'winget' falhar. Aqui resolvemos o
    caminho real do executável para funcionar em qualquer contexto.
    """
    p = shutil.which("winget")
    if p and os.path.exists(p):
        return p

    local = os.environ.get("LOCALAPPDATA", "")
    if local:
        alias = os.path.join(local, "Microsoft", "WindowsApps", "winget.exe")
        if os.path.exists(alias):
            return alias

    pf = os.environ.get("ProgramFiles", r"C:\Program Files")
    pattern = os.path.join(pf, "WindowsApps",
                           "Microsoft.DesktopAppInstaller_*_x64__8wekyb3d8bbwe",
                           "winget.exe")
    candidates = sorted(glob.glob(pattern))
    if candidates:
        return candidates[-1]
    return None


def install_software(winget_id, status_callback=None):
    """Instala um app via winget. Retorna True se instalado (ou já presente)."""
    friendly = _friendly_name(winget_id)
    if status_callback:
        status_callback(f"📦 Instalando {friendly}...")

    winget = _find_winget()
    if not winget:
        if status_callback:
            status_callback("❌ winget não encontrado. Instale o 'App Installer' pela Microsoft Store.")
        return False

    cmd = [
        winget, "install", "-e", "--id", winget_id,
        "--silent", "--accept-package-agreements", "--accept-source-agreements",
        "--disable-interactivity",
    ]
    try:
        result = subprocess.run(
            cmd, creationflags=CREATE_NO_WINDOW,
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=900,
        )
        rc = result.returncode
        out = ((result.stdout or "") + "\n" + (result.stderr or "")).lower()

        if rc == 0:
            if status_callback:
                status_callback(f"✅ {friendly} instalado com sucesso.")
            return True

        # Códigos/mensagens que significam "já instalado / nada a fazer"
        already = ("already installed" in out or "já está instalad" in out
                   or "no available upgrade" in out or "no newer package" in out)
        if already:
            if status_callback:
                status_callback(f"✅ {friendly} já estava instalado.")
            return True

        if "no package found" in out or "nenhum pacote" in out or "no applicable" in out:
            if status_callback:
                status_callback(f"⚠️ {friendly}: não encontrado no catálogo winget.")
            return False

        # Erro real — mostra a última linha significativa
        linhas = [l.strip() for l in (result.stdout or result.stderr or "").splitlines() if l.strip()]
        detalhe = linhas[-1][:120] if linhas else f"código {rc}"
        if status_callback:
            status_callback(f"⚠️ Falha em {friendly}: {detalhe}")
        return False

    except subprocess.TimeoutExpired:
        if status_callback:
            status_callback(f"⏱️ Timeout ao instalar {friendly} (excedeu 15 min).")
        return False
    except Exception as e:
        if status_callback:
            status_callback(f"❌ Erro ao instalar {friendly}: {e}")
        return False

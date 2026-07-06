import os
import sys
import shutil
import re

def main():
    if len(sys.argv) < 2:
        print("Uso: python builder.py [PORTABLE|HOST]")
        sys.exit(1)
        
    mode = sys.argv[1].upper()
    if mode not in ["PORTABLE", "HOST"]:
        print("Modo invalido. Use PORTABLE ou HOST.")
        sys.exit(1)
        
    # 1. Altera temporariamente a flag no build_config.py
    config_path = os.path.join("gear", "build_config.py")
    with open(config_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Substitui a linha EDICAO_ATUAL
    content = re.sub(r'EDICAO_ATUAL\s*=\s*".*"', f'EDICAO_ATUAL = "{mode}"', content)
    
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"[*] Flag EDICAO_ATUAL definida para: {mode}")
    
    # 2. Extrai a versão atual para o nome dinâmico
    version = "1.0.1"
    updater_path = os.path.join("gear", "updater.py")
    if os.path.exists(updater_path):
        with open(updater_path, "r", encoding="utf-8") as uf:
            for line in uf:
                if line.startswith("CURRENT_VERSION"):
                    version = line.split("=")[1].strip().strip('"').strip("'")
                    break

    # 3. Executa o PyInstaller com configuracoes limpas
    exe_name = f"SysForge_{mode.capitalize()}_v{version}"
    
    # 2.5 Generate version_info.txt dynamically
    ver_parts = version.split(".")
    while len(ver_parts) < 4:
        ver_parts.append("0")
    ver_tuple = f"{ver_parts[0]}, {ver_parts[1]}, {ver_parts[2]}, {ver_parts[3]}"
    
    version_info_content = f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({ver_tuple}),
    prodvers=({ver_tuple}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'041604b0',
        [StringStruct(u'CompanyName', u'Singularity Dot'),
        StringStruct(u'FileDescription', u'SysForge - Motor de Implantacao TI'),
        StringStruct(u'FileVersion', u'{version}.0'),
        StringStruct(u'InternalName', u'SysForge'),
        StringStruct(u'LegalCopyright', u'Copyright (c) 2026 Singularity Dot'),
        StringStruct(u'OriginalFilename', u'{exe_name}.exe'),
        StringStruct(u'ProductName', u'SysForge'),
        StringStruct(u'ProductVersion', u'{version}.0')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1046, 1200])])
  ]
)"""
    with open("version_info.txt", "w", encoding="utf-8") as vf:
        vf.write(version_info_content)

    # Montando o comando do pyinstaller com os parametros solicitados e dependencias
    cmd = (
        f'pyinstaller --noconfirm --onefile --noconsole --uac-admin --name "{exe_name}" '
        f'--icon "icon.ico" '
        f'--version-file "version_info.txt" '
        f'--add-data "gui;gui" --add-data "gear;gear" --add-data "worker;worker" '
        f'--add-data "OfficeInstall;OfficeInstall" '
        f'--add-data "icon.ico;." '
        f'--add-data "icon.png;." '
    )
    
    # Se for PORTABLE, podemos excluir bibliotecas pesadas aqui (ex: --exclude-module=opencv)
    if mode == "PORTABLE":
        cmd += '--exclude-module=matplotlib --exclude-module=numpy --exclude-module=pandas '
        
    cmd += 'main.py'
    
    print(f"[*] Compilando {exe_name}...")
    print(f"[*] Comando: {cmd}")
    
    exit_code = os.system(cmd)
    
    if exit_code != 0:
        print("[!] Erro durante a compilacao.")
        sys.exit(1)
        
    # 3. Limpeza Cirurgica (Obrigatório)
    print("\n[*] Iniciando limpeza de cache (Regra 1)...")
    
    build_dir = "build"
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
        print(f"[-] Pasta removida: {build_dir}/")
        
    spec_file = f"{exe_name}.spec"
    if os.path.exists(spec_file):
        os.remove(spec_file)
        print(f"[-] Arquivo removido: {spec_file}")
        
    if os.path.exists("version_info.txt"):
        os.remove("version_info.txt")
        print(f"[-] Arquivo removido: version_info.txt")
        
    print(f"\n[+] Build {mode} concluido com sucesso! O executavel esta limpo na pasta 'dist/'.\n")

if __name__ == "__main__":
    main()

"""
Retomada automática da instalação do Office após reboot.

Fluxo:
  1. A Esterilização remove o Office antigo (deleta o serviço C2R, que só some
     de fato após reiniciar). Por isso a reinstalação limpa exige um reboot.
  2. arm_resume() copia o executável para uma pasta fixa (%ProgramData%\\SysForge)
     — assim funciona tanto no Host quanto no Portable, mesmo sem o pendrive — e
     registra um gatilho RunOnce que dispara UMA vez no próximo logon.
  3. No boot, o SysForge é iniciado com --resume-office → run_resume_office()
     abre uma janela mínima, conclui a instalação/ativação e limpa o estado.

O RunOnce se auto-remove após disparar (o Windows apaga a entrada antes de
executá-la), o que elimina qualquer risco de loop de boot.
"""

import os
import sys
import json
import shutil
import subprocess
import winreg

CREATE_NO_WINDOW = 0x08000000

APP_NAME = "SysForge"
RESUME_DIR = os.path.join(os.environ.get("ProgramData", r"C:\ProgramData"), APP_NAME)
STATE_FILE = os.path.join(RESUME_DIR, "resume_office.json")
RESUME_EXE = os.path.join(RESUME_DIR, "SysForge_Resume.exe")

_RUNONCE_KEY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce"
_RUNONCE_VALUE = "SysForgeResumeOffice"

MAX_ATTEMPTS = 2


def _current_exe():
    """Caminho do exe compilado, ou None se rodando como script (.py em dev)."""
    if getattr(sys, "frozen", False):
        return sys.executable
    return None


def arm_resume(activate=True):
    """Prepara a retomada pós-reboot. Retorna True se armado com sucesso."""
    exe = _current_exe()
    if not exe:
        return False  # modo dev: não há exe para retomar

    try:
        os.makedirs(RESUME_DIR, exist_ok=True)

        # Copia o exe para local fixo (funciona sem depender do pendrive)
        target_exe = RESUME_EXE
        if os.path.abspath(exe) != os.path.abspath(RESUME_EXE):
            try:
                shutil.copy2(exe, RESUME_EXE)
            except Exception:
                target_exe = exe  # fallback: usa o exe atual (ideal no Host)

        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump({"action": "install_office",
                       "activate": bool(activate),
                       "attempts": 0}, f)

        cmd = f'"{target_exe}" --resume-office'
        key = winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, _RUNONCE_KEY, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, _RUNONCE_VALUE, 0, winreg.REG_SZ, cmd)
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


def is_resume_pending():
    return os.path.exists(STATE_FILE)


def read_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _bump_attempts():
    st = read_state() or {"attempts": 0}
    st["attempts"] = int(st.get("attempts", 0)) + 1
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(st, f)
    except Exception:
        pass
    return st["attempts"]


def clear_resume():
    """Remove estado + gatilho (idempotente)."""
    try:
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
    except Exception:
        pass
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, _RUNONCE_KEY, 0, winreg.KEY_SET_VALUE)
        try:
            winreg.DeleteValue(key, _RUNONCE_VALUE)
        except OSError:
            pass
        winreg.CloseKey(key)
    except Exception:
        pass


def request_reboot(seconds=8):
    """Agenda o reinício do Windows."""
    try:
        subprocess.run(
            ["shutdown", "/r", "/t", str(seconds),
             "/c", "SysForge: reiniciando para concluir a instalacao do Office."],
            creationflags=CREATE_NO_WINDOW, check=False,
        )
        return True
    except Exception:
        return False


def run_resume_office():
    """Executado no boot (flag --resume-office): janela mínima que conclui o Office."""
    state = read_state()
    if not state:
        return

    if _bump_attempts() > MAX_ATTEMPTS:
        clear_resume()
        return

    import queue
    import threading
    import customtkinter as ctk

    ctk.set_appearance_mode("Light")
    win = ctk.CTk()
    win.title("SysForge — Instalação do Office")
    w, h = 520, 280
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    win.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")
    win.resizable(False, False)
    win.attributes("-topmost", True)

    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ico = os.path.join(base, "icon.ico")
    if os.path.exists(ico):
        try:
            win.iconbitmap(ico)
        except Exception:
            pass

    ctk.CTkLabel(win, text="Continuando a instalação do Office",
                 font=("Helvetica", 18, "bold"), text_color="#000000").pack(pady=(28, 6))
    ctk.CTkLabel(win, text="Não desligue o computador. Isso pode levar alguns minutos.",
                 font=("Consolas", 12), text_color="#333333").pack(pady=(0, 18))
    lbl = ctk.CTkLabel(win, text="Preparando...", font=("Consolas", 12), text_color="#000000")
    lbl.pack(pady=(0, 10))
    prog = ctk.CTkProgressBar(win, width=420, progress_color="#D50000")
    prog.set(0)
    prog.pack(pady=(0, 10))

    uiq = queue.Queue()

    def _status(m):
        uiq.put(("status", m))

    def _progress(p):
        uiq.put(("progress", p))

    def _work():
        try:
            from gear.office_deploy import install_and_activate_office
            install_and_activate_office(_status, _progress)
        except Exception as e:
            uiq.put(("status", f"❌ Erro: {e}"))
        uiq.put(("done", None))

    def _pump():
        try:
            while True:
                kind, val = uiq.get_nowait()
                if kind == "status":
                    lbl.configure(text=str(val)[:70])
                elif kind == "progress":
                    try:
                        prog.set(min(float(val), 1.0))
                    except Exception:
                        pass
                elif kind == "done":
                    clear_resume()
                    lbl.configure(text="✅ Concluído. Esta janela fecha em instantes.")
                    prog.set(1.0)
                    win.after(5000, win.destroy)
                    return
        except queue.Empty:
            pass
        win.after(150, _pump)

    threading.Thread(target=_work, daemon=True).start()
    win.after(150, _pump)
    win.mainloop()

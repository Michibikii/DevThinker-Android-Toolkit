import os
import threading
import customtkinter as ctk
import infrastructure.adb_client as adb_client
from ui.widgets import ToolTip, ToastNotification, center_toplevel
from infrastructure import (
    ConfigManager,
    check_adb_update,
    download_and_install_adb,
    find_adb,
    get_adb_url_and_sys,
    refresh_adb_path,
    run_adb,
    set_manual_adb_path,
    uninstall_adb,
)


def _write_log(filename: str, msg: str):
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        log_dir = os.path.join(base_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, filename)
        with open(log_path, "a", encoding="utf-8") as f:
            from datetime import datetime
            f.write(f"[{datetime.now().isoformat()}] {msg}\n")
    except Exception:
        pass


def crash_log(msg: str):
    _write_log("crash.log", msg)


def device_log(msg: str):
    _write_log("device.log", msg)


def connection_log(msg: str):
    _write_log("connection.log", msg)


def ui_log(msg: str):
    _write_log("ui.log", msg)


def adb_log(msg: str):
    _write_log("adb.log", msg)


def __getattr__(name):
    if name == "ADB_PATH":
        return adb_client.ADB_PATH
    raise AttributeError(name)


def _kill_adb_process():
    return adb_client._kill_adb_process()

def run_async(task_func, callback_func=None, app=None):
    def wrapper():
        try:
            result = task_func()
            if callback_func and app:
                def safe_cb():
                    try:
                        callback_func(result)
                    except:
                        pass
                app.after(0, safe_cb)
        except:
            pass
    threading.Thread(target=wrapper, daemon=True).start()

def requires_device(func):
    def wrapper(self, *args, **kwargs):
        if not self.app.current_device_id:
            show_alert(self.app, "Advertencia", "No hay dispositivo conectado", is_error=False)
            return
        return func(self, *args, **kwargs)
    return wrapper

def center_toplevel(win, parent, w, h):
    parent.update_idletasks()
    win.update_idletasks()
    x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (w // 2)
    y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (h // 2)
    win.geometry(f"{w}x{h}+{x}+{y}")

class AskYesNo(ctk.CTkToplevel):
    def __init__(self, parent, title, text):
        super().__init__(parent)
        self.title(title)
        self.attributes("-topmost", True)
        self.transient(parent)
        self.result = False
        center_toplevel(self, parent, 400, 150)
        
        ctk.CTkLabel(self, text=text, font=("Segoe UI", 14), wraplength=350).pack(pady=20, padx=20, expand=True)
        f = ctk.CTkFrame(self, fg_color="transparent")
        f.pack(fill="x", pady=10)
        ctk.CTkButton(f, text="Sí", font=("Segoe UI", 13, "bold"), width=100, fg_color="#e74c3c", hover_color="#c0392b", command=self.yes).pack(side="left", expand=True, padx=10)
        ctk.CTkButton(f, text="No", font=("Segoe UI", 13, "bold"), width=100, fg_color="#475569", hover_color="#334155", command=self.no).pack(side="right", expand=True, padx=10)
        self.grab_set()
        self.wait_window()

    def yes(self):
        self.result = True
        self.destroy()

    def no(self):
        self.result = False
        self.destroy()

    def get(self):
        return self.result

class AskString(ctk.CTkToplevel):
    def __init__(self, parent, title, text, initial_value=""):
        super().__init__(parent)
        self.title(title)
        self.attributes("-topmost", True)
        self.transient(parent)
        self.result = None
        center_toplevel(self, parent, 400, 180)
        
        ctk.CTkLabel(self, text=text, font=("Segoe UI", 14)).pack(pady=(20, 10))
        self.entry = ctk.CTkEntry(self, width=300)
        self.entry.pack(pady=5)
        if initial_value:
            self.entry.insert(0, initial_value)
            self.entry.select_range(0, "end")
        self.entry.focus()
        
        f = ctk.CTkFrame(self, fg_color="transparent")
        f.pack(fill="x", pady=15)
        ctk.CTkButton(f, text="Aceptar", font=("Segoe UI", 13, "bold"), width=100, fg_color="#38BDF8", hover_color="#0284C7", command=self.ok).pack(side="left", expand=True, padx=10)
        ctk.CTkButton(f, text="Cancelar", font=("Segoe UI", 13, "bold"), width=100, fg_color="#475569", hover_color="#334155", command=self.cancel).pack(side="right", expand=True, padx=10)
        self.bind("<Return>", lambda e: self.ok())
        self.grab_set()
        self.wait_window()

    def ok(self):
        self.result = self.entry.get()
        self.destroy()

    def cancel(self):
        self.result = None
        self.destroy()

    def get(self):
        return self.result

class ShowInfo(ctk.CTkToplevel):
    def __init__(self, parent, title, text, is_error=False):
        super().__init__(parent)
        self.title(title)
        self.attributes("-topmost", True)
        self.transient(parent)
        center_toplevel(self, parent, 400, 180)
        
        c = "#EF4444" if is_error else "#10B981"
        ctk.CTkLabel(self, text=title, font=("Segoe UI", 16, "bold"), text_color=c).pack(pady=(20, 5))
        ctk.CTkLabel(self, text=text, font=("Segoe UI", 13), wraplength=350).pack(pady=5, padx=20, expand=True)
        ctk.CTkButton(self, text="Aceptar", font=("Segoe UI", 13, "bold"), width=100, fg_color="#38BDF8", hover_color="#0284C7", command=self.destroy).pack(pady=15)
        self.bind("<Return>", lambda e: self.destroy())
        self.grab_set()
        self.wait_window()


def show_alert(parent, title, text, is_error=False):
    ShowInfo(parent, title, text, is_error=is_error)


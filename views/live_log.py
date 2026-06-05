import customtkinter as ctk
import threading
import utils 
from utils import ToolTip
from services import LiveLogService

class FrameLiveLog(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.process = None
        self.is_running = False
        self.service = LiveLogService()

        ctk.CTkLabel(self, text="Logcat en Vivo", font=("Segoe UI", 24, "bold"), text_color="#F8FAFC").pack(anchor="w", pady=(0, 5))
        ctk.CTkLabel(self, text="Ve todo lo que pasa en tu teléfono en tiempo real.", font=("Segoe UI", 13), text_color="#94A3B8").pack(anchor="w", pady=(0, 15))
        
        toolbar = ctk.CTkFrame(self, fg_color="#181D2B", corner_radius=12, border_width=1, border_color="#252D40")
        toolbar.pack(fill="x", pady=5)
        
        self.btn_toggle = ctk.CTkButton(toolbar, text="▶ Iniciar Lectura", width=160, height=40, font=("Segoe UI", 13, "bold"), fg_color="#10B981", hover_color="#059669", command=self.toggle)
        self.btn_toggle.pack(side="left", padx=15, pady=15)
        
        btn_clear = ctk.CTkButton(toolbar, text="🧹 Limpiar", width=120, height=40, font=("Segoe UI", 13, "bold"), fg_color="#F59E0B", hover_color="#D97706", command=self.clear)
        btn_clear.pack(side="left", padx=(0, 15), pady=15)
        
        btn_copy = ctk.CTkButton(toolbar, text="📋 Copiar", width=110, height=40, font=("Segoe UI", 13, "bold"), fg_color="#64748B", hover_color="#475569", command=self.copy_all)
        btn_copy.pack(side="left", padx=(0, 15), pady=15)
        
        self.chk_errors = ctk.CTkCheckBox(toolbar, text="Solo Errores/Crashes", font=("Segoe UI", 13, "bold"), text_color="#EF4444", fg_color="#EF4444", hover_color="#DC2626", border_color="#EF4444")
        self.chk_errors.pack(side="left", padx=10, pady=15)
        self.chk_errors.select()
        
        self.entry_filter = ctk.CTkEntry(toolbar, placeholder_text="Filtrar por palabra...", width=200, height=40, font=("Segoe UI", 12), fg_color="#0B0F19", border_color="#252D40", text_color="#F8FAFC")
        self.entry_filter.pack(side="right", padx=15, pady=15)

        self.txt_log = ctk.CTkTextbox(self, font=("Consolas", 12), text_color="#E2E8F0", fg_color="#0B0F19", border_width=1, border_color="#252D40", corner_radius=12)
        self.txt_log.pack(fill="both", expand=True, pady=15)
        self.txt_log.tag_config("error", foreground="#EF4444")
        self.txt_log.tag_config("warn", foreground="#F59E0B")
        self.txt_log.configure(state="disabled")

    def toggle(self):
        if self.is_running:
            self.stop()
        else:
            self.start()
    
    def start(self):
        if not self.app.current_device_id: 
            utils.show_alert(self.app, "Advertencia", "Sin dispositivo conectado.", is_error=False)
            return

        if not self.service.adb_ready():
            utils.show_alert(self.app, "Error", "No se encontró ADB en el sistema.", is_error=True)
            return
            
        self.is_running = True
        self.btn_toggle.configure(text="⏹ Detener", fg_color="#EF4444", hover_color="#DC2626")
        
        self.txt_log.configure(state="normal")
        self.txt_log.delete("1.0", "end")
        self.txt_log.configure(state="disabled")
        
        cmd = self.service.build_logcat_command(self.app.current_device_id)
        threading.Thread(target=self.run, args=(cmd,), daemon=True).start()

    def stop(self):
        self.is_running = False
        if self.process: 
            try:
                self.process.terminate()
            except:
                pass
        try:
            self.btn_toggle.configure(text="▶ Iniciar", fg_color="#10B981", hover_color="#059669")
        except:
            pass

    def run(self, cmd):
        try:
            self.process = self.service.start_logcat_process(cmd)
            for line in self.process.stdout:
                if not self.is_running:
                    break

                keep, tag = self.service.should_keep_line(
                    line,
                    errors_only=bool(self.chk_errors.get()),
                    filter_text=self.entry_filter.get().strip(),
                )
                if not keep:
                    continue

                try:
                    self.app.after(0, self._safe_insert, line, tag)
                except:
                    pass
        except:
            pass
        self.stop()

    def _safe_insert(self, line, tags):
        try:
            self.txt_log.configure(state="normal")
            self.txt_log.insert("end", line, tags)
            if self.txt_log.yview()[1] > 0.9:
                self.txt_log.see("end")
            self.txt_log.configure(state="disabled")
        except:
            pass

    def clear(self): 
        self.service.clear_logcat(self.app.current_device_id)
        self.txt_log.configure(state="normal")
        self.txt_log.delete("1.0", "end")
        self.txt_log.configure(state="disabled")
    
    def copy_all(self):
        self.clipboard_clear()
        self.clipboard_append(self.txt_log.get("1.0", "end"))
        self.app.show_toast("¡Log copiado al portapapeles!", color="#38BDF8")
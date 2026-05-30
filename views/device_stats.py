import customtkinter as ctk
import threading
import time
from utils import ToolTip
from services import DeviceMonitorService

class FrameDeviceStats(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.is_monitoring = False
        self.monitor_thread = None

        ctk.CTkLabel(self, text="Monitor del Sistema", font=("Segoe UI", 24, "bold"), text_color="#F8FAFC").pack(anchor="w", pady=(0, 5))
        ctk.CTkLabel(self, text="Supervisa el uso de RAM, Almacenamiento y CPU en tiempo real.", font=("Segoe UI", 13), text_color="#94A3B8").pack(anchor="w", pady=(0, 15))

        c = ctk.CTkFrame(self, fg_color="#181D2B", corner_radius=12, border_width=1, border_color="#252D40")
        c.pack(fill="x", pady=5)
        
        self.btn_toggle = ctk.CTkButton(c, text="▶ Iniciar Monitor", width=160, height=40, fg_color="#10B981", hover_color="#059669", font=("Segoe UI", 13, "bold"), command=self.toggle_monitor)
        self.btn_toggle.pack(side="left", padx=15, pady=15)
        ToolTip(self.btn_toggle, "Inicia o detiene la lectura en tiempo real del hardware del teléfono.")

        self.btn_clear = ctk.CTkButton(c, text="🧹 Limpiar", width=110, height=40, font=("Segoe UI", 13, "bold"), fg_color="#475569", hover_color="#334155", command=self.clear_monitor)
        self.btn_clear.pack(side="left", padx=(0, 15), pady=15)
        ToolTip(self.btn_clear, "Detiene el monitor y limpia los gráficos y registros de la pantalla.")

        self.grid_cards = ctk.CTkFrame(self, fg_color="transparent")
        self.grid_cards.pack(fill="x", pady=15)
        self.grid_cards.grid_columnconfigure(0, weight=1)
        self.grid_cards.grid_columnconfigure(1, weight=1)

        card_ram = ctk.CTkFrame(self.grid_cards, fg_color="#181D2B", corner_radius=12, border_width=1, border_color="#252D40")
        card_ram.grid(row=0, column=0, padx=(0, 8), sticky="nsew")
        ctk.CTkLabel(card_ram, text="🧠 Memoria RAM", font=("Segoe UI", 15, "bold"), text_color="#F8FAFC").pack(anchor="w", padx=20, pady=(20, 5))
        self.bar_ram = ctk.CTkProgressBar(card_ram, progress_color="#38BDF8", fg_color="#0B0F19", height=12)
        self.bar_ram.pack(fill="x", padx=20, pady=10)
        self.bar_ram.set(0)
        self.lbl_ram_text = ctk.CTkLabel(card_ram, text="-- / -- MB (0%)", font=("Segoe UI", 12), text_color="#94A3B8")
        self.lbl_ram_text.pack(anchor="w", padx=20, pady=(0, 20))

        card_sto = ctk.CTkFrame(self.grid_cards, fg_color="#181D2B", corner_radius=12, border_width=1, border_color="#252D40")
        card_sto.grid(row=0, column=1, padx=(8, 0), sticky="nsew")
        ctk.CTkLabel(card_sto, text="💾 Almacenamiento Interno", font=("Segoe UI", 15, "bold"), text_color="#F8FAFC").pack(anchor="w", padx=20, pady=(20, 5))
        self.bar_sto = ctk.CTkProgressBar(card_sto, progress_color="#8B5CF6", fg_color="#0B0F19", height=12)
        self.bar_sto.pack(fill="x", padx=20, pady=10)
        self.bar_sto.set(0)
        self.lbl_sto_text = ctk.CTkLabel(card_sto, text="-- / -- GB (0%)", font=("Segoe UI", 12), text_color="#94A3B8")
        self.lbl_sto_text.pack(anchor="w", padx=20, pady=(0, 20))

        ctk.CTkLabel(self, text="Uso de CPU (Top Procesos)", font=("Segoe UI", 15, "bold"), text_color="#F8FAFC").pack(anchor="w", pady=(15, 8))
        self.txt_cpu = ctk.CTkTextbox(self, font=("Consolas", 12), fg_color="#0B0F19", text_color="#E2E8F0", border_width=1, border_color="#252D40", corner_radius=12)
        self.txt_cpu.pack(fill="both", expand=True)
        self.txt_cpu.insert("1.0", "Haz clic en 'Iniciar Monitor' para ver los procesos...")
        self.txt_cpu.configure(state="disabled")

    def clear_monitor(self):
        if self.is_monitoring:
            self.toggle_monitor()
        
        self.bar_ram.set(0)
        self.lbl_ram_text.configure(text="-- / -- MB (0%)")
        
        self.bar_sto.set(0)
        self.lbl_sto_text.configure(text="-- / -- GB (0%)")
        
        self.txt_cpu.configure(state="normal")
        self.txt_cpu.delete("1.0", "end")
        self.txt_cpu.insert("end", "Haz clic en 'Iniciar Monitor' para ver los procesos...")
        self.txt_cpu.configure(state="disabled")

    def toggle_monitor(self):
        if not self.app.current_device_id and not self.is_monitoring:
            utils.show_alert(self.app, "Advertencia", "No hay dispositivo conectado.", is_error=False)
            return

        if self.is_monitoring:
            self.is_monitoring = False
            self.btn_toggle.configure(text="▶ Iniciar Monitor", fg_color="#10B981", hover_color="#059669")
        else:
            self.is_monitoring = True
            self.btn_toggle.configure(text="⏹ Detener Monitor", fg_color="#EF4444", hover_color="#DC2626")
            self.txt_cpu.configure(state="normal")
            self.txt_cpu.delete("1.0", "end")
            self.txt_cpu.insert("end", "Cargando datos...\n")
            self.txt_cpu.configure(state="disabled")
            
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()

    def _monitor_loop(self):
        while self.is_monitoring:
            if not self.app.current_device_id:
                for _ in range(30):
                    if not self.is_monitoring:
                        break
                    time.sleep(0.1)
                continue

            try:
                if not self.is_monitoring: break
                stats = DeviceMonitorService.build_system_stats(self.app.current_device_id)

                if self.is_monitoring:
                    try:
                        self.app.after(0, self._update_ui, stats)
                    except:
                        pass
                
            except:
                pass
            
            for _ in range(30):
                if not self.is_monitoring:
                    break
                time.sleep(0.1)

        try:
            self.app.after(0, lambda: self.btn_toggle.configure(text="▶ Iniciar Monitor", fg_color="#10B981", hover_color="#059669"))
        except:
            pass

    def _update_ui(self, stats):
        if not self.is_monitoring:
            return

        if stats.total_ram > 0:
            used_ram = stats.total_ram - stats.avail_ram
            ram_pct = used_ram / stats.total_ram
            self.bar_ram.set(ram_pct)
            self.lbl_ram_text.configure(text=f"{int(used_ram)} MB / {int(stats.total_ram)} MB ({int(ram_pct * 100)}%)")

        if stats.sto_pct > 0:
            self.bar_sto.set(stats.sto_pct / 100.0)
            self.lbl_sto_text.configure(text=f"{stats.sto_used} / {stats.sto_total} ({stats.sto_pct}%)")

        self.txt_cpu.configure(state="normal")
        self.txt_cpu.delete("1.0", "end")
        self.txt_cpu.insert("end", stats.cpu_text)
        self.txt_cpu.configure(state="disabled")
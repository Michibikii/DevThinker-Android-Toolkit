import customtkinter as ctk
import threading
from utils import ToolTip, run_async
from services import HardwareService

class FrameHardwareInfo(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        ctk.CTkLabel(self, text="Información de Hardware", font=("Segoe UI", 24, "bold"), text_color="#F8FAFC").pack(anchor="w", pady=(0, 5))
        ctk.CTkLabel(self, text="Obtiene detalles técnicos sobre la batería, pantalla, sistema y sensores del dispositivo.", font=("Segoe UI", 13), text_color="#94A3B8").pack(anchor="w", pady=(0, 15))

        toolbar = ctk.CTkFrame(self, fg_color="#181D2B", corner_radius=12, border_width=1, border_color="#252D40")
        toolbar.pack(fill="x", pady=5)
        
        self.btn_refresh = ctk.CTkButton(toolbar, text="🔄 Refrescar Datos", width=160, height=40, font=("Segoe UI", 13, "bold"), fg_color="#38BDF8", hover_color="#0284C7", command=self.load_data)
        self.btn_refresh.pack(side="left", padx=15, pady=15)

        self.scrollable_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scrollable_frame.pack(fill="both", expand=True, pady=10)

        sys_card = ctk.CTkFrame(self.scrollable_frame, fg_color="#181D2B", corner_radius=12, border_width=1, border_color="#252D40")
        sys_card.pack(fill="x", pady=5)
        ctk.CTkLabel(sys_card, text="⚙️ Sistema y Hardware", font=("Segoe UI", 16, "bold"), text_color="#F8FAFC").pack(anchor="w", padx=20, pady=(15, 10))
        
        sys_grid = ctk.CTkFrame(sys_card, fg_color="transparent")
        sys_grid.pack(fill="x", padx=20, pady=(0, 15))
        sys_grid.grid_columnconfigure(0, weight=1)
        sys_grid.grid_columnconfigure(1, weight=1)

        self.lbl_manufacturer = self._create_info_row(sys_grid, "Fabricante", 0, 0)
        self.lbl_model = self._create_info_row(sys_grid, "Modelo", 0, 1)
        self.lbl_android_ver = self._create_info_row(sys_grid, "Versión Android", 1, 0)
        self.lbl_cpu = self._create_info_row(sys_grid, "Plataforma/CPU", 1, 1)

        batt_card = ctk.CTkFrame(self.scrollable_frame, fg_color="#181D2B", corner_radius=12, border_width=1, border_color="#252D40")
        batt_card.pack(fill="x", pady=10)
        ctk.CTkLabel(batt_card, text="🔋 Batería", font=("Segoe UI", 16, "bold"), text_color="#F8FAFC").pack(anchor="w", padx=20, pady=(15, 10))
        
        batt_grid = ctk.CTkFrame(batt_card, fg_color="transparent")
        batt_grid.pack(fill="x", padx=20, pady=(0, 15))
        batt_grid.grid_columnconfigure(0, weight=1)
        batt_grid.grid_columnconfigure(1, weight=1)
        batt_grid.grid_columnconfigure(2, weight=1)

        self.lbl_batt_level = self._create_info_row(batt_grid, "Nivel", 0, 0)
        self.lbl_batt_health = self._create_info_row(batt_grid, "Salud", 0, 1)
        self.lbl_batt_status = self._create_info_row(batt_grid, "Estado", 0, 2)
        self.lbl_batt_temp = self._create_info_row(batt_grid, "Temperatura", 1, 0)
        self.lbl_batt_volt = self._create_info_row(batt_grid, "Voltaje", 1, 1)

        disp_card = ctk.CTkFrame(self.scrollable_frame, fg_color="#181D2B", corner_radius=12, border_width=1, border_color="#252D40")
        disp_card.pack(fill="x", pady=5)
        ctk.CTkLabel(disp_card, text="📱 Pantalla", font=("Segoe UI", 16, "bold"), text_color="#F8FAFC").pack(anchor="w", padx=20, pady=(15, 10))
        
        disp_grid = ctk.CTkFrame(disp_card, fg_color="transparent")
        disp_grid.pack(fill="x", padx=20, pady=(0, 15))
        disp_grid.grid_columnconfigure(0, weight=1)
        disp_grid.grid_columnconfigure(1, weight=1)

        self.lbl_resolution = self._create_info_row(disp_grid, "Resolución", 0, 0)
        self.lbl_density = self._create_info_row(disp_grid, "Densidad", 0, 1)

        sens_card = ctk.CTkFrame(self.scrollable_frame, fg_color="#181D2B", corner_radius=12, border_width=1, border_color="#252D40")
        sens_card.pack(fill="x", pady=10)
        ctk.CTkLabel(sens_card, text="📡 Sensores Disponibles", font=("Segoe UI", 16, "bold"), text_color="#F8FAFC").pack(anchor="w", padx=20, pady=(15, 5))
        
        self.txt_sensors = ctk.CTkTextbox(sens_card, font=("Consolas", 12), fg_color="#0B0F19", text_color="#E2E8F0", border_width=1, border_color="#252D40", corner_radius=8, height=150)
        self.txt_sensors.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        self.txt_sensors.insert("1.0", "Haz clic en 'Refrescar Datos' para cargar la lista de sensores...")
        self.txt_sensors.configure(state="disabled")

    def _create_info_row(self, parent, title, row, col):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, sticky="w", pady=5)
        ctk.CTkLabel(frame, text=f"{title}:", font=("Segoe UI", 13, "bold"), text_color="#94A3B8").pack(side="left", padx=(0, 10))
        lbl_value = ctk.CTkLabel(frame, text="--", font=("Segoe UI", 14), text_color="#F8FAFC")
        lbl_value.pack(side="left")
        return lbl_value

    def load_data(self):
        if not self.app.current_device_id:
            return

        self.btn_refresh.configure(state="disabled", text="Cargando...")
        
        def fetch_task():
            return HardwareService.get_hardware_info(self.app.current_device_id)

        def update_ui(info):
            self.lbl_manufacturer.configure(text=info.manufacturer)
            self.lbl_model.configure(text=info.model)
            self.lbl_android_ver.configure(text=info.android_version)
            self.lbl_cpu.configure(text=info.cpu_platform)
            
            self.lbl_batt_level.configure(text=info.battery_level)
            self.lbl_batt_health.configure(text=info.battery_health)
            self.lbl_batt_status.configure(text=info.battery_status)
            self.lbl_batt_temp.configure(text=info.battery_temp)
            self.lbl_batt_volt.configure(text=info.battery_voltage)
            
            self.lbl_resolution.configure(text=info.screen_resolution)
            self.lbl_density.configure(text=info.screen_density)

            self.txt_sensors.configure(state="normal")
            self.txt_sensors.delete("1.0", "end")
            self.txt_sensors.insert("end", info.sensors_list)
            self.txt_sensors.configure(state="disabled")

            self.btn_refresh.configure(state="normal", text="🔄 Refrescar Datos")

        run_async(fetch_task, update_ui, self.app)

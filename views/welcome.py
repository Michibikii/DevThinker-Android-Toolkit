import customtkinter as ctk


class FrameWelcome(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        hero = ctk.CTkFrame(self, fg_color="#0B0F19", corner_radius=18, border_width=1, border_color="#252D40")
        hero.pack(fill="x", padx=10, pady=(0, 18))

        ctk.CTkLabel(hero, text="Bienvenido a DevThinker", font=("Segoe UI", 30, "bold"), text_color="#F8FAFC").pack(anchor="w", padx=28, pady=(26, 6))
        ctk.CTkLabel(hero, text="Tu hub de Android para conectar, inspeccionar y administrar dispositivos con ADB desde una interfaz limpia.", font=("Segoe UI", 14), text_color="#94A3B8", wraplength=820, justify="left").pack(anchor="w", padx=28, pady=(0, 18))

        actions = ctk.CTkFrame(hero, fg_color="transparent")
        actions.pack(anchor="w", padx=28, pady=(0, 24))

        ctk.CTkButton(actions, text="📡 Conectar Dispositivo", height=44, width=200, font=("Segoe UI", 13, "bold"), fg_color="#38BDF8", hover_color="#0284C7", command=lambda: self.app.show_frame("wireless")).pack(side="left", padx=(0, 12))
        ctk.CTkButton(actions, text="🔧 Abrir Utilidades", height=44, width=180, font=("Segoe UI", 13, "bold"), fg_color="#8B5CF6", hover_color="#7C3AED", command=lambda: self.app.show_frame("tools")).pack(side="left", padx=(0, 12))
        ctk.CTkButton(actions, text="📊 Ir al Panel Principal", height=44, width=200, font=("Segoe UI", 13, "bold"), fg_color="#10B981", hover_color="#059669", command=self.open_panel).pack(side="left")

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=10)
        grid.grid_columnconfigure((0, 1), weight=1)

        self._card(grid, 0, 0, "Conexión", "Escanea QR, conecta por IP o usa USB.")
        self._card(grid, 0, 1, "Explorador", "Gestiona archivos, crea carpetas y mueve contenido.")
        self._card(grid, 1, 0, "Herramientas", "Captura, scrcpy, texto y acciones rápidas.")
        self._card(grid, 1, 1, "Monitoreo", "RAM, CPU, almacenamiento y logcat en vivo.")

    def _card(self, parent, row, col, title, body):
        card = ctk.CTkFrame(parent, fg_color="#181D2B", corner_radius=14, border_width=1, border_color="#252D40")
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(card, text=title, font=("Segoe UI", 16, "bold"), text_color="#F8FAFC").pack(anchor="w", padx=20, pady=(18, 4))
        ctk.CTkLabel(card, text=body, font=("Segoe UI", 12), text_color="#94A3B8", wraplength=300, justify="left").pack(anchor="w", padx=20, pady=(0, 18))

    def open_panel(self):
        if self.app.current_device_id:
            self.app.show_frame("stats")
        else:
            self.app.show_frame("wireless")

import customtkinter as ctk


RECENT_OPTION_DETAILS = {
    "wireless": ("Conexión", "Escanea QR, conecta por IP o usa USB."),
    "files": ("Explorador", "Gestiona archivos, crea carpetas y mueve contenido."),
    "tools": ("Utilidades", "Captura, scrcpy, texto y acciones rápidas."),
    "stats": ("Monitoreo", "RAM, CPU, almacenamiento y logcat en vivo."),
    "live": ("Logcat en Vivo", "Revisa eventos y errores en tiempo real."),
    "analyze": ("Análisis", "Detecta errores y revisa fallos comunes."),
    "packages": ("Paquetes", "Instala, desinstala y gestiona apps."),
    "terminal": ("Terminal", "Ejecuta comandos ADB directamente."),
}


class FrameWelcome(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        hero = ctk.CTkFrame(self, fg_color="#0B0F19", corner_radius=18, border_width=1, border_color="#252D40")
        hero.pack(fill="x", padx=10, pady=(0, 18))

        ctk.CTkLabel(hero, text="Bienvenido a DevThinker", font=("Segoe UI", 30, "bold"), text_color="#F8FAFC").pack(anchor="w", padx=28, pady=(26, 6))
        ctk.CTkLabel(hero, text="Tu hub de Android para conectar, inspeccionar y administrar dispositivos con ADB desde una interfaz limpia.", font=("Segoe UI", 14), text_color="#94A3B8", wraplength=820, justify="left").pack(anchor="w", padx=28, pady=(0, 18))

        actions = ctk.CTkFrame(hero, fg_color="transparent")
        actions.pack(fill="x", padx=28, pady=(0, 24))

        self.connect_btn = ctk.CTkButton(actions, text="📡 Conectar Dispositivo", height=44, font=("Segoe UI", 13, "bold"), fg_color="#38BDF8", hover_color="#0284C7", command=lambda: self.app.show_frame("wireless"))
        self.connect_btn.pack(fill="x")

        self.recent_block = ctk.CTkFrame(self, fg_color="transparent")
        self.recent_block.pack(fill="x", padx=10, pady=(0, 18))
        self.recent_title = ctk.CTkLabel(self.recent_block, text="Opciones usadas recientemente", font=("Segoe UI", 14, "bold"), text_color="#F8FAFC")
        self.recent_title.pack(anchor="w", pady=(6, 6))

        self.recent_grid = ctk.CTkFrame(self.recent_block, fg_color="#181D2B", corner_radius=14, border_width=1, border_color="#252D40")
        self.recent_grid.pack(fill="x")
        self.recent_empty_label = ctk.CTkLabel(self.recent_grid, text="No hay opciones usadas recientemente", font=("Segoe UI", 13), text_color="#94A3B8")
        self.recent_empty_label.grid(row=0, column=0, columnspan=2, padx=24, pady=28)
        self.recent_cards = []
        for index in range(4):
            card = ctk.CTkFrame(self.recent_grid, fg_color="#181D2B", corner_radius=14, border_width=1, border_color="#252D40")
            card_title = ctk.CTkLabel(card, text="", font=("Segoe UI", 16, "bold"), text_color="#F8FAFC")
            card_title.pack(anchor="w", padx=20, pady=(18, 4))
            card_body = ctk.CTkLabel(card, text="", font=("Segoe UI", 12), text_color="#94A3B8", wraplength=300, justify="left")
            card_body.pack(anchor="w", padx=20, pady=(0, 18))
            self.recent_cards.append({"frame": card, "title": card_title, "body": card_body, "target": None})

        self.refresh_state()

    def _card(self, parent, row, col, title, body):
        card = ctk.CTkFrame(parent, fg_color="#181D2B", corner_radius=14, border_width=1, border_color="#252D40")
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(card, text=title, font=("Segoe UI", 16, "bold"), text_color="#F8FAFC").pack(anchor="w", padx=20, pady=(18, 4))
        ctk.CTkLabel(card, text=body, font=("Segoe UI", 12), text_color="#94A3B8", wraplength=300, justify="left").pack(anchor="w", padx=20, pady=(0, 18))

    def _bind_card_click(self, widget, target_frame):
        def go(_event=None):
            self.app.show_frame(target_frame)

        widget.bind("<Button-1>", go)
        for child in widget.winfo_children():
            child.bind("<Button-1>", go)
            for grandchild in child.winfo_children():
                grandchild.bind("<Button-1>", go)

    def _recent_items(self):
        recent_tabs = getattr(getattr(self.app, "app_state", None), "recent_tabs", [])
        items = []

        for name in recent_tabs:
            data = RECENT_OPTION_DETAILS.get(name)
            if data is None:
                continue
            items.append((name, data[0], data[1]))

        return items

    def refresh_recent_options(self):
        items = self._recent_items()
        if not items:
            for card_state in self.recent_cards:
                card_state["frame"].grid_remove()
                card_state["target"] = None
            self.recent_grid.configure(fg_color="#181D2B", border_width=1, border_color="#252D40")
            self.recent_empty_label.grid(row=0, column=0, columnspan=2, padx=24, pady=28)
            return

        self.recent_empty_label.grid_remove()
        self.recent_grid.configure(fg_color="transparent", border_width=0)

        for column in range(2):
            self.recent_grid.grid_columnconfigure(column, weight=1)

        for index, card_state in enumerate(self.recent_cards):
            if index >= len(items):
                card_state["frame"].grid_remove()
                card_state["target"] = None
                continue

            name, title, body = items[index]
            card_state["title"].configure(text=title)
            card_state["body"].configure(text=body)
            card_state["target"] = name
            row = index // 2
            col = index % 2
            card_state["frame"].grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            self._bind_card_click(card_state["frame"], name)

        for index in range(len(items), len(self.recent_cards)):
            self.recent_cards[index]["frame"].grid_remove()

    def open_panel(self):
        if self.app.current_device_id:
            self.app.show_frame("stats")
        else:
            self.app.show_frame("wireless")

    def refresh_state(self):
        try:
            if getattr(self.app, "current_device_id", None):
                self.connect_btn.pack_forget()
            else:
                if not self.connect_btn.winfo_ismapped():
                    self.connect_btn.pack(fill="x")
        except Exception:
            pass

import customtkinter as ctk
from utils import ToolTip
from services import AnalyzerService

class FrameAnalyzer(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        ctk.CTkLabel(self, text="Análisis Profundo de Errores", font=("Segoe UI", 24, "bold"), text_color="#F8FAFC").pack(anchor="w", pady=(0, 5))
        
        info_text = (
            "Cómo usar:\n"
            "1. Si tu app crasheó, ve a la pestaña 'Logcat en Vivo' y copia el texto rojo de error.\n"
            "2. Pega ese texto abajo.\n"
            "3. Haz clic en 'Analizar Traza' para que identifique el archivo y línea responsable."
        )
        ctk.CTkLabel(self, text=info_text, font=("Segoe UI", 13), text_color="#94A3B8", justify="left").pack(anchor="w", pady=(0, 15))
        
        self.txt_input = ctk.CTkTextbox(self, height=120, text_color="#64748B", fg_color="#0B0F19", border_width=1, border_color="#252D40", corner_radius=12, font=("Consolas", 12))
        self.txt_input.pack(fill="x", pady=10)
        self.txt_input.insert("1.0", "[Pega el registro de error o stack trace aquí...]")
        
        self.txt_input.bind("<FocusIn>", self.on_focus)
        self.txt_input.bind("<FocusOut>", self.on_unfocus)
        
        btn = ctk.CTkButton(self, text="⚡ Analizar Traza", width=160, height=40, font=("Segoe UI", 13, "bold"), fg_color="#38BDF8", hover_color="#0284C7", command=self.analyze)
        btn.pack(anchor="w", pady=10)

        
        ctk.CTkLabel(self, text="Reporte de Análisis:", font=("Segoe UI", 15, "bold"), text_color="#F8FAFC").pack(anchor="w", pady=(20, 8))
        self.res = ctk.CTkTextbox(self, fg_color="#0B0F19", text_color="#E2E8F0", border_width=1, border_color="#252D40", corner_radius=12, font=("Consolas", 13))
        self.res.pack(fill="both", expand=True, pady=5)
        self.res.configure(state="disabled")

    def on_focus(self, event):
        if self.txt_input.get("1.0", "end-1c") == AnalyzerService.PLACEHOLDER:
            self.txt_input.delete("1.0", "end")
            self.txt_input.configure(text_color="#E2E8F0")

    def on_unfocus(self, event):
        if not self.txt_input.get("1.0", "end-1c").strip():
            self.txt_input.configure(text_color="#64748B")
            self.txt_input.insert("1.0", AnalyzerService.PLACEHOLDER)

    def analyze(self):
        log = self.txt_input.get("1.0", "end")
        
        self.res.configure(state="normal")
        report = AnalyzerService.analyze_log(log)
        self.res.delete("1.0", "end")
        self.res.insert("end", report)
        self.res.configure(state="disabled")
import customtkinter as ctk


def center_toplevel(win, parent, w, h):
    parent.update_idletasks()
    win.update_idletasks()
    x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (w // 2)
    y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (h // 2)
    win.geometry(f"{w}x{h}+{x}+{y}")


class ToolTip:
    def __init__(self, widget, text, delay=600):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tip_window = None
        self.id = None
        self._bind_widget(widget)

    def _bind_widget(self, widget):
        widget.bind("<Enter>", self.schedule, add="+")
        widget.bind("<Leave>", self.hide, add="+")
        widget.bind("<ButtonPress>", self.hide, add="+")
        for child in widget.winfo_children():
            self._bind_widget(child)

    def schedule(self, event=None):
        self.unschedule()
        self.id = self.widget.after(self.delay, self.show)

    def unschedule(self):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

    def show(self):
        if self.tip_window or not self.text:
            return
        try:
            x = self.widget.winfo_rootx() + 20
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 10
            self.tip_window = ctk.CTkToplevel(self.widget)
            self.tip_window.wm_overrideredirect(True)
            self.tip_window.wm_geometry(f"+{x}+{y}")
            self.tip_window.attributes('-topmost', True)
            self.tip_window.lift()
            label = ctk.CTkLabel(self.tip_window, text=self.text, justify='left', fg_color="#181D2B", text_color="#F8FAFC", border_width=1, border_color="#252D40", corner_radius=6, font=("Segoe UI", 11))
            label.pack(ipadx=8, ipady=4)
        except:
            self.hide()

    def hide(self, event=None):
        self.unschedule()
        if self.tip_window:
            try:
                self.tip_window.destroy()
            except:
                pass
            self.tip_window = None


class ToastNotification(ctk.CTkFrame):
    def __init__(self, parent, message, color="#10B981"):
        super().__init__(parent, fg_color=color, corner_radius=10)
        parent.update_idletasks()
        try:
            x = parent.winfo_rootx() + parent.winfo_width() - 320
            y = parent.winfo_rooty() + parent.winfo_height() - 70
            self.place(x=x, y=y, width=300, height=50)
        except:
            self.place(x=0, y=0, width=300, height=50)

        f = ctk.CTkFrame(self, fg_color=color, corner_radius=10)
        f.pack(fill="both", expand=True)
        ctk.CTkLabel(f, text=message, font=("Segoe UI", 13, "bold"), text_color="white").pack(expand=True)
        self.after(2500, self.destroy)

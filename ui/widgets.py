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
        self._check_id = None
        
        self.widget.bind("<Enter>", self.schedule, add="+")
        self.widget.bind("<Leave>", self.hide, add="+")
        self.widget.bind("<ButtonPress>", self.hide, add="+")
        for child in self.widget.winfo_children():
            child.bind("<Enter>", self.schedule, add="+")
            child.bind("<Leave>", self.hide, add="+")
            child.bind("<ButtonPress>", self.hide, add="+")

    def schedule(self, event=None):
        if self.id is not None or self.tip_window is not None:
            return
        self.id = self.widget.after(self.delay, self.show)

    def unschedule(self):
        if self.id:
            try:
                self.widget.after_cancel(self.id)
            except:
                pass
            self.id = None
        if self._check_id:
            try:
                self.widget.after_cancel(self._check_id)
            except:
                pass
            self._check_id = None

    def show(self):
        self.id = None
        if self.tip_window or not self.text:
            return
        try:
            import tkinter as tk
            x = self.widget.winfo_rootx() + 20
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 10
            
            self.tip_window = tk.Toplevel(self.widget)
            self.tip_window.wm_overrideredirect(True)
            self.tip_window.wm_geometry(f"+{x}+{y}")
            self.tip_window.attributes('-topmost', True)
            
            display_text = self.text + "   "
            label = tk.Label(self.tip_window, text=display_text, justify='left',
                             background="#181D2B", foreground="#F8FAFC",
                             font=("Segoe UI", 10), borderwidth=1, relief="solid",
                             highlightbackground="#252D40", highlightthickness=1)
            label.pack(ipadx=8, ipady=4)
            self.tip_window.update_idletasks()
            
            self._check_id = self.widget.after(100, self.check_hover)
        except:
            self.hide()

    def check_hover(self):
        try:
            px = self.widget.winfo_pointerx()
            py = self.widget.winfo_pointery()
            rx = self.widget.winfo_rootx()
            ry = self.widget.winfo_rooty()
            rw = self.widget.winfo_width()
            rh = self.widget.winfo_height()
            
            if rx <= px <= rx + rw and ry <= py <= ry + rh:
                self._check_id = self.widget.after(100, self.check_hover)
                return
        except:
            pass
        self.hide()

    def hide(self, event=None):
        try:
            if event and hasattr(event, "x_root") and hasattr(event, "y_root"):
                px, py = event.x_root, event.y_root
                rx = self.widget.winfo_rootx()
                ry = self.widget.winfo_rooty()
                rw = self.widget.winfo_width()
                rh = self.widget.winfo_height()
                if rx <= px <= rx + rw and ry <= py <= ry + rh:
                    return
        except:
            pass

        self.unschedule()
        if self.tip_window:
            try:
                self.tip_window.destroy()
            except:
                pass
            self.tip_window = None


class ToastNotification(ctk.CTkFrame):
    _active_toasts = []

    def __init__(self, parent, message, color="#10B981"):
        super().__init__(parent, fg_color=color, corner_radius=10)
        self.parent_win = parent
        
        ToastNotification._active_toasts = [t for t in ToastNotification._active_toasts if t.winfo_exists()]
        ToastNotification._active_toasts.append(self)
        ToastNotification.reposition_all()

        f = ctk.CTkFrame(self, fg_color=color, corner_radius=10)
        f.pack(fill="both", expand=True)
        ctk.CTkLabel(f, text=message, font=("Segoe UI", 13, "bold"), text_color="white").pack(expand=True)
        self.after(2500, self.close)

    def close(self):
        if self in ToastNotification._active_toasts:
            ToastNotification._active_toasts.remove(self)
        try:
            self.destroy()
        except:
            pass
        ToastNotification.reposition_all()

    @classmethod
    def reposition_all(cls):
        cls._active_toasts = [t for t in cls._active_toasts if t.winfo_exists()]
        if not cls._active_toasts:
            return
            
        parent = cls._active_toasts[0].parent_win
        try:
            pw = parent.winfo_width()
            ph = parent.winfo_height()
        except:
            pw, ph = 800, 600

        base_y = ph - 70
        for i, toast in enumerate(reversed(cls._active_toasts)):
            try:
                toast.place(x=max(pw - 320, 10), y=max(base_y - (i * 60), 10), width=300, height=50)
            except:
                pass


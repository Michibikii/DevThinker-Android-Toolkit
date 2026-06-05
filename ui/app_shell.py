import customtkinter as ctk

from core import visible_nav_items
from views import (
    FrameAnalyzer,
    FrameDeviceStats,
    FrameFileExplorer,
    FrameLiveLog,
    FramePackages,
    FrameTerminal,
    FrameTools,
    FrameWireless,
    FrameWelcome,
    FrameHardwareInfo,
)


def build_shell(app):
    app.sidebar = ctk.CTkFrame(app, corner_radius=0, fg_color="#111522")
    app.sidebar.grid(row=0, column=0, sticky="nsew")

    ctk.CTkLabel(app.sidebar, text="🧠 DevThinker", font=("Segoe UI", 26, "bold"), text_color="#E2E8F0").pack(pady=(40, 25))

    app.info_card = ctk.CTkFrame(app.sidebar, fg_color="#181D2B", corner_radius=12, border_width=1, border_color="#252D40")
    app.info_card.pack(fill="x", padx=18, pady=(0, 20))

    app.lbl_model = ctk.CTkLabel(app.info_card, text="🚫 Sin Dispositivo", font=("Segoe UI", 15, "bold"), text_color="#F8FAFC", anchor="w", justify="left", wraplength=190)
    app.lbl_model.pack(fill="x", padx=15, pady=(15, 2))

    app.lbl_sub1 = ctk.CTkLabel(app.info_card, text="Esperando conexión...", font=("Segoe UI", 12), text_color="#94A3B8", anchor="w", justify="left", wraplength=190)
    app.lbl_sub1.pack(fill="x", padx=15, pady=0)

    app.lbl_sub2 = ctk.CTkLabel(app.info_card, text="", font=("Segoe UI", 11), text_color="#64748B", anchor="w", justify="left", wraplength=190)
    app.lbl_sub2.pack(fill="x", padx=15, pady=(2, 15))

    app.btn_disconnect = ctk.CTkButton(app.info_card, text="Desconectar", fg_color="#EF4444", hover_color="#DC2626", height=28, font=("Segoe UI", 12, "bold"), command=app.disconnect_device)

    app.nav_frame = ctk.CTkScrollableFrame(app.sidebar, fg_color="transparent")
    app.nav_frame.pack(fill="both", expand=True)
    app.nav_btns = {}

    ctk.CTkLabel(app.sidebar, text="Premium", font=("Segoe UI", 10), text_color="#475569").pack(side="bottom", pady=15)

    app.container = ctk.CTkFrame(app, fg_color="#111522", corner_radius=16, border_width=1, border_color="#1E2538")
    app.container.grid(row=0, column=1, sticky="nsew", padx=25, pady=25)

    app.frames = {
        "welcome": FrameWelcome(app.container, app),
        "live": FrameLiveLog(app.container, app),
        "analyze": FrameAnalyzer(app.container),
        "files": FrameFileExplorer(app.container, app),
        "stats": FrameDeviceStats(app.container, app),
        "hardware": FrameHardwareInfo(app.container, app),
        "wireless": FrameWireless(app.container, app),
        "packages": FramePackages(app.container, app),
        "terminal": FrameTerminal(app.container, app),
        "tools": FrameTools(app.container, app),
    }


def render_menu(app):
    for widget in app.nav_frame.winfo_children():
        widget.destroy()

    try:
        import utils

        utils.ui_log(f"render_menu current_tab={app.current_tab!r} connected={bool(app.current_device_id)}")
    except Exception:
        pass

    app.nav_btns = {}
    for item in visible_nav_items(bool(app.current_device_id)):
        text = item["text"]
        name = item["name"]
        needs_device = item.get("needs_device", False)
        enabled = (not needs_device) or bool(app.current_device_id)
        btn = ctk.CTkButton(
            app.nav_frame,
            text=text,
            height=42,
            anchor="w",
            fg_color="transparent",
            text_color="#94A3B8",
            hover_color="#1E293B",
            corner_radius=8,
            font=("Segoe UI", 14),
            state="normal" if enabled else "disabled",
            command=lambda n=name: app.show_frame(n),
        )
        btn.pack(fill="x", padx=18, pady=4)
        if not enabled:
            btn.configure(text_color_disabled="#64748B")
        app.nav_btns[name] = btn

    if app.current_tab in app.nav_btns:
        app.nav_btns[app.current_tab].configure(fg_color="#1E293B", text_color="#38BDF8", font=("Segoe UI", 14, "bold"))


def show_frame(app, name, record_recent=True):
    from core import frame_requires_device

    if frame_requires_device(name) and not app.current_device_id:
        return

    try:
        import utils

        utils.ui_log(f"show_frame request name={name!r} record_recent={record_recent} connected={bool(app.current_device_id)}")
    except Exception:
        pass

    app.current_tab = name
    if record_recent and hasattr(app, "record_recent_tab"):
        app.record_recent_tab(name)

    for btn_name, btn in app.nav_btns.items():
        btn.configure(fg_color="transparent", text_color="#94A3B8", font=("Segoe UI", 14, "normal"))
    if name in app.nav_btns:
        app.nav_btns[name].configure(fg_color="#1E293B", text_color="#38BDF8", font=("Segoe UI", 14, "bold"))

    for frame in app.frames.values():
        frame.pack_forget()

    app.frames[name].pack(fill="both", expand=True, padx=25, pady=25)

    if name == "tools":
        app.frames["tools"].refresh_adb_card_ui()
    elif name == "files" and app.current_device_id:
        app.frames["files"].load_files()
    elif name == "hardware" and app.current_device_id:
        app.frames["hardware"].load_data()
    elif name == "packages" and app.current_device_id:
        if not getattr(app.frames["packages"], "items", None):
            app.frames["packages"].refresh()


def sync_connection_ui(app, connected):
    try:
        import utils

        utils.ui_log(f"sync_connection_ui connected={connected} current_tab={app.current_tab!r}")
    except Exception:
        pass

    if connected:
        app.lbl_sub2.pack_configure(pady=(2, 10))
        app.btn_disconnect.pack(fill="x", padx=15, pady=(0, 15))
    else:
        app.btn_disconnect.pack_forget()
        app.lbl_sub2.pack_configure(pady=(2, 15))
    render_menu(app)
    app.frames["tools"].refresh_feature_states()

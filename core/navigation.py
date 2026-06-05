NAV_ITEMS = [
    {"text": "🏠  Inicio", "name": "welcome", "needs_device": False, "visible_when_connected": False},
    {"text": "📡  Conectar Dispositivo", "name": "wireless", "needs_device": False, "visible_when_connected": False},
    {"text": "📱  Hardware", "name": "hardware", "needs_device": True},
    {"text": "📊  Monitor", "name": "stats", "needs_device": True},
    {"text": "🔴  Logcat en Vivo", "name": "live", "needs_device": True},
    {"text": "🔎  Análisis", "name": "analyze", "needs_device": True},
    {"text": "💻  Terminal ADB", "name": "terminal", "needs_device": True},
    {"text": "📁  Explorador", "name": "files", "needs_device": True},
    {"text": "📦  Paquetes", "name": "packages", "needs_device": True},
    {"text": "🔧  Utilidades", "name": "tools", "needs_device": False},
]


def frame_requires_device(name):
    return name in {"hardware", "stats", "live", "analyze", "terminal", "files", "packages"}


def visible_nav_items(device_connected):
    items = []
    for item in NAV_ITEMS:
        if item["name"] == "wireless" and device_connected:
            continue
        items.append(item)
    return items

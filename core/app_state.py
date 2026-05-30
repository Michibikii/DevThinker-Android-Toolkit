from dataclasses import dataclass, field


@dataclass
class AppState:
    current_device_id: str | None = None
    current_tab: str = "welcome"
    is_monitoring: bool = True
    adb_update_available: bool = False
    last_state: bool = False
    cached_dev_id: str | None = None
    cached_full_name: str = ""
    cached_market_name: str = ""
    cached_ver: str = "?"
    cached_api: str = "?"
    cached_cpu: str = "?"
    cached_battery: str = "?"
    bat_counter: int = 5
    recent_tabs: list[str] = field(default_factory=list)
    device_state: dict = field(default_factory=dict)

    def reset_device(self):
        self.current_device_id = None
        self.cached_dev_id = None
        self.device_state = {}
        self.bat_counter = 5

    def set_recent_tabs(self, tabs):
        self.recent_tabs = [tab for tab in tabs if isinstance(tab, str) and tab and tab != "welcome"]

    def record_recent_tab(self, name, max_items=4):
        if name == "welcome":
            return False

        self.recent_tabs = [tab for tab in self.recent_tabs if tab != name]
        self.recent_tabs.insert(0, name)
        self.recent_tabs = self.recent_tabs[:max_items]
        return True

    def set_connected(self, device_id, full_name, market_name, ver, api, cpu, battery):
        self.current_device_id = device_id
        self.cached_dev_id = device_id
        self.cached_full_name = full_name
        self.cached_market_name = market_name
        self.cached_ver = ver
        self.cached_api = api
        self.cached_cpu = cpu
        self.cached_battery = battery
        self.device_state = {
            "dev_id": device_id,
            "full_name": full_name,
            "market_name": market_name,
            "model": market_name,
            "ver": ver,
            "api": api,
            "cpu": cpu,
            "battery": battery,
        }

    def sync_battery_counter(self, refreshed: bool):
        if refreshed:
            self.bat_counter = 0
        else:
            self.bat_counter += 1

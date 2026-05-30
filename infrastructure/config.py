import json
import os
import sys

def _resolve_project_root():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


PROJECT_ROOT = _resolve_project_root()
CONFIG_FILE = os.path.join(PROJECT_ROOT, "config.json")


class ConfigManager:
    _cache = None

    @staticmethod
    def _write_full_config(data):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f)
            return True
        except:
            return False

    @staticmethod
    def load_config():
        if ConfigManager._cache is not None:
            return ConfigManager._cache.copy()

        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        ConfigManager._cache = loaded
                    else:
                        ConfigManager._cache = {}
                        ConfigManager._write_full_config(ConfigManager._cache)
                    return ConfigManager._cache.copy()
            except:
                ConfigManager._cache = {}
                ConfigManager._write_full_config(ConfigManager._cache)
                return {}

        ConfigManager._cache = {}
        ConfigManager._write_full_config(ConfigManager._cache)
        return {}

    @staticmethod
    def save_config(key, value):
        data = ConfigManager.load_config()
        data[key] = value
        ConfigManager._cache = data.copy()
        ConfigManager._write_full_config(data)

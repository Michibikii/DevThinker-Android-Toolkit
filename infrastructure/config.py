import json
import os

CONFIG_FILE = "config.json"


class ConfigManager:
    _cache = None

    @staticmethod
    def load_config():
        if ConfigManager._cache is not None:
            return ConfigManager._cache.copy()
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    ConfigManager._cache = json.load(f)
                    return ConfigManager._cache.copy()
            except:
                pass
        ConfigManager._cache = {}
        return {}

    @staticmethod
    def save_config(key, value):
        data = ConfigManager.load_config()
        data[key] = value
        ConfigManager._cache = data.copy()
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except:
            pass

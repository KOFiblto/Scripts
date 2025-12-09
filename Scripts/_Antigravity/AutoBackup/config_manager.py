import json
import os

CONFIG_FILE = "config.json"

class ConfigManager:
    def __init__(self, config_file=CONFIG_FILE):
        self.config_file = config_file
        self.default_config = {
            "source_paths": [],
            "destination_path": "",
            "auto_backup_enabled": False,
            "last_backup_timestamp": None
        }
        self.config = self.load_config()

    def load_config(self):
        if not os.path.exists(self.config_file):
            return self.default_config.copy()
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return self.default_config.copy()

    def save_config(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except IOError as e:
            print(f"Error saving config: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save_config()

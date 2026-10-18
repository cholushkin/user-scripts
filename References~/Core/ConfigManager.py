import os
import json

class ConfigManager:
    def __init__(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # ScriptUtils/
        self.default_config_path = os.path.join(base_dir, "Config", "default_config.json")
        self.user_config_path = os.path.join(base_dir, "Config", "user_config.json")
        self.config = {}        
        self.load_config()
        
    def load_config(self):
        self.config = self.load_json(self.default_config_path)

        if os.path.exists(self.user_config_path):
            user_config = self.load_json(self.user_config_path)
            self.override_config(user_config)
        return self.config

    def load_json(self, path):
        if not os.path.exists(path):
            print(f"Warning: {path} not found.")
            return {}
        with open(path, 'r') as file:
            return json.load(file)

    def override_config(self, user_config):
        for key, value in user_config.items():            
            self.config[key] = value

 
            
    def print(self):
        print("\nFinal Merged Configuration:")
        print(json.dumps(self.config, indent=4))

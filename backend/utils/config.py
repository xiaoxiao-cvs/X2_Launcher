import json
from pathlib import Path

class Config:
    def __init__(self):
        self.config_path = Path("config.json")
        self.config = self.load_config()

    def load_config(self):
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "default_version": "latest",
            "github_token": "your_personal_access_token_here"
        }

    def save_config(self):
        if "default_version" not in self.config:
            self.config["default_version"] = "latest"
        if "github_token" not in self.config:
            self.config["github_token"] = "your_personal_access_token_here"
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4)

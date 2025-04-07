import json
import logging
from pathlib import Path
import os

class Settings:
    def __init__(self):
        self.settings_path = Path("settings.json")
        # 确保assets目录存在
        assets_dir = Path("assets")
        if not assets_dir.exists():
            assets_dir.mkdir(parents=True)
            
        # 设置默认背景图片
        default_bg = assets_dir / "background.jpg"
        if not default_bg.exists():
            # 创建一个纯色背景
            from PIL import Image
            img = Image.new('RGB', (1920, 1080), color='#2b2b2b')
            img.save(default_bg)
        
        self._default_settings = {
            "appearance": {
                "background_image": str(default_bg),
                "transparency": 0.7,  # 降低默认透明度
                "theme": "dark",
                "accent_color": "#1E90FF",
                "window_size": "1280x720"
            },
            "deployment": {
                "auto_check_update": True,
                "python_version": "3.13.0",
                "install_path": "maibot_versions",
                "repo_url": "https://github.com/MaiM-with-u/MaiBot.git"
            }
        }
        self.settings = self.load_settings()
        
    def load_settings(self):
        try:
            if self.settings_path.exists():
                with open(self.settings_path, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    return self._merge_settings(self._default_settings, loaded_settings)
            return self._default_settings.copy()
        except Exception as e:
            logging.error(f"加载设置失败: {e}")
            return self._default_settings.copy()

    def save_settings(self):
        try:
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logging.error(f"保存设置失败: {e}")
            raise

    def _merge_settings(self, default, custom):
        result = default.copy()
        for key, value in custom.items():
            if key in result and isinstance(result[key], dict):
                result[key] = self._merge_settings(result[key], value)
            else:
                result[key] = value
        return result

    def get(self, *keys):
        value = self.settings
        for key in keys:
            value = value.get(key)
            if value is None:
                return None
        return value

    def set(self, value, *keys):
        target = self.settings
        for key in keys[:-1]:
            target = target.setdefault(key, {})
        target[keys[-1]] = value
        self.save_settings()

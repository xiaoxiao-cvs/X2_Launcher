import json
import logging
from pathlib import Path
import os
from typing import Any, Dict, Optional
from .logger import XLogger  # 将 logger 改为 XLogger
import configparser

class AppConfig:
    CONFIG_FILE = Path(__file__).parent.parent / "config.json"

    def __init__(self):
        self.settings_path = Path("settings.json")
        self.assets_dir = Path("assets")
        self.config = configparser.ConfigParser()
        
        # 配置文件路径
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        self.config_file = os.path.join(self.base_dir, "config.ini")
        
        # 默认配置
        self._setup_defaults()
        
        # 加载配置文件
        self._load_config()
        
    def _initialize_defaults(self):
        """初始化默认配置"""
        self._ensure_assets_dir()
        bg_path = self._ensure_default_background()
        
        self._config = {
            "appearance": {
                "background_image": str(bg_path),
                "transparency": 0.7,
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
    
    def _ensure_assets_dir(self) -> None:
        """确保assets目录存在"""
        if not self.assets_dir.exists():
            self.assets_dir.mkdir(parents=True)
            
    def _ensure_default_background(self) -> Path:
        """确保默认背景图片存在"""
        bg_path = self.assets_dir / "background.jpg"
        if not bg_path.exists():
            from PIL import Image
            img = Image.new('RGB', (1920, 1080), color='#2b2b2b')
            img.save(bg_path)
        return bg_path

    def get(self, section: str, key: str, fallback: Optional[Any] = None) -> Any:
        """获取配置值，支持默认值"""
        try:
            if fallback is not None:
                return self.config.get(section, key, fallback=fallback)
            return self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            if fallback is not None:
                return fallback
            return None
    
    def set(self, section: str, key: str, value: Any) -> None:
        """设置配置值"""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, value)
        self.save()
        
    def update_section(self, section: str, values: Dict[str, Any]) -> None:
        """更新整个配置区块"""
        if section in self._config:
            self._config[section].update(values)
            self.save()
            
    def _load_config(self) -> None:
        """从文件加载配置"""
        try:
            if self.settings_path.exists():
                with open(self.settings_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    self._merge_config(loaded_config)
            if os.path.exists(self.config_file):
                self.config.read(self.config_file)
        except Exception as e:
            logging.error(f"配置加载失败: {e}")
            
    def _merge_config(self, new_config: Dict) -> None:
        """合并配置"""
        for section, values in new_config.items():
            if section in self._config:
                if isinstance(self._config[section], dict):
                    self._config[section].update(values)
                else:
                    self._config[section] = values
            else:
                self._config[section] = values
                
    def save(self) -> None:
        """保存配置到文件"""
        try:
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
            with open(self.config_file, 'w') as f:
                self.config.write(f)
        except Exception as e:
            logging.error(f"配置保存失败: {e}")
            
    def get_all(self) -> Dict:
        """获取所有配置"""
        return self._config.copy()
        
    def reset_section(self, section: str) -> None:
        """重置某个配置区块为默认值"""
        if section in self._config:
            self._initialize_defaults()
            self.save()

    @classmethod
    def load_config(cls):
        """加载配置文件"""
        try:
            if not cls.CONFIG_FILE.exists():
                default_config = {
                    "default_version": "latest",
                    "github_token": ""
                }
                with open(cls.CONFIG_FILE, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=4)
                return default_config
                
            with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            XLogger.log(f"配置加载失败: {e}", "ERROR")
            return {}
    
    @classmethod
    def save_config(cls, config):
        """保存配置文件"""
        try:
            with open(cls.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
            return True
        except Exception as e:
            XLogger.log(f"配置保存失败: {e}", "ERROR")
            return False

    def _setup_defaults(self):
        """设置默认配置"""
        self.config["deployment"] = {
            "repo_url": "https://github.com/MaiM-with-u/MaiBot.git",
            "install_path": os.path.join(self.base_dir, "maibot_versions")
        }
        
        self.config["github"] = {
            "token": ""
        }

    @staticmethod
    def load_config():
        """加载配置并返回字典"""
        config = {}
        app_config = AppConfig()
        
        # 将配置转换为字典格式
        for section in app_config.config.sections():
            config[section] = {}
            for key, value in app_config.config.items(section):
                config[section][key] = value
        
        return config

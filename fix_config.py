"""
修复X2_Launcher配置的脚本
"""
import os
import configparser
from pathlib import Path

def fix_config():
    """修复配置文件"""
    print("开始修复配置文件...")
    
    # 项目根目录
    base_dir = Path(__file__).resolve().parent
    config_path = os.path.join(base_dir, "config.ini")
    
    # 创建配置
    config = configparser.ConfigParser()
    
    # 设置默认值
    config["deployment"] = {
        "repo_url": "https://github.com/MaiM-with-u/MaiBot.git",
        "install_path": os.path.join(base_dir, "maibot_versions")
    }
    
    config["github"] = {
        "token": ""  # 可以填入GitHub令牌以提高API限制
    }
    
    # 保存到文件
    with open(config_path, 'w') as f:
        config.write(f)
    
    print(f"配置文件已创建: {config_path}")
    print("配置已修复，请重启应用")

if __name__ == "__main__":
    fix_config()

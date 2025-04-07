import os
import logging
from pathlib import Path
import requests
import asyncio

async def setup_environment():
    """异步初始化环境"""
    try:
        # 在这里添加需要的异步初始化操作
        await asyncio.sleep(0.1)  # 给事件循环一个运行的机会
        return True
    except Exception as e:
        logging.error(f"环境初始化失败: {e}")
        return False

def check_network():
    """检查网络连接"""
    try:
        response = requests.get("https://api.github.com", timeout=5)
        return response.status_code == 200
    except:
        return False

def setup_environment():
    """设置运行环境"""
    # 确保必要的目录存在
    dirs = ['assets', 'logs', 'maibot_versions']
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    
    # 配置日志
    log_file = Path("logs/deploy.log")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

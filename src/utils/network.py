import requests
from ..logger import logger

def check_network(timeout=5):
    """检查网络连接状态"""
    try:
        requests.get("https://github.com", timeout=timeout)
        return True
    except:
        logger.log("网络连接检查失败", "WARNING")
        return False

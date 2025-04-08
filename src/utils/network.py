import asyncio
import socket
from src.logger import XLogger

async def check_network(timeout=5):
    """检查网络连接"""
    try:
        # 测试与github的连接
        socket.create_connection(("github.com", 443), timeout=timeout)
        XLogger.log("网络连接正常", "INFO")
        return True
    except OSError:
        XLogger.log("无法连接到github.com", "ERROR")
        return False
    except Exception as e:
        XLogger.log(f"网络检查异常: {e}", "ERROR")
        return False

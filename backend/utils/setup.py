import asyncio
from .logger import XLogger
from .network import check_network

async def setup_environment():
    """初始化运行环境"""
    try:
        # 检查网络连接
        if not await check_network():
            XLogger.log("网络连接异常，请检查网络设置", "WARNING")
            return False
        
        XLogger.log("环境初始化完成", "INFO")
        return True
        
    except Exception as e:
        XLogger.log(f"环境初始化失败: {e}", "ERROR")
        return False
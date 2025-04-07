import os
import logging
from pathlib import Path
import requests
import asyncio
from typing import Optional
from .logger import logger

async def setup_environment() -> None:
    """异步环境初始化"""
    try:
        # 创建必要的目录
        dirs = [
            'assets',
            'maibot_versions',
            'logs'
        ]
        
        for dir_name in dirs:
            path = Path(dir_name)
            path.mkdir(parents=True, exist_ok=True)
            logger.log(f"检查目录: {dir_name}")
            
        # 检查网络连接
        await check_network()
        
    except Exception as e:
        logger.log(f"环境初始化失败: {e}", "ERROR")

async def check_network() -> bool:
    """检查网络连接"""
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.github.com', timeout=5) as resp:
                if resp.status == 200:
                    logger.log("网络连接正常")
                else:
                    logger.log("网络连接异常", "WARNING")
    except Exception as e:
        logger.log(f"网络检查失败: {e}", "WARNING")

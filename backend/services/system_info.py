# -*- coding: utf-8 -*-
"""
系统信息服务
提供系统状态、性能监控等功能
"""
import os
import sys
import time
import logging
import asyncio
from typing import Dict, Any

logger = logging.getLogger("x2-launcher.system-info")

class SystemInfoService:
    """系统信息服务类"""
    
    def __init__(self):
        """初始化系统信息服务"""
        self.last_metrics = {}
        self.missing_psutil = False
        
        # 尝试导入psutil
        try:
            import psutil
            self.psutil = psutil
        except ImportError:
            logger.warning("psutil模块未安装，将使用模拟数据")
            self.psutil = None
            self.missing_psutil = True
    
    async def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        # 这里可以实现实际检查服务状态的逻辑
        # 例如检查MongoDB、NapCat等服务是否运行
        
        # 示例实现，返回模拟数据
        return {
            "mongodb": {"status": "running", "info": "本地实例"},
            "napcat": {"status": "running", "info": "端口 8095"},
            "nonebot": {"status": "stopped", "info": ""},
            "maibot": {"status": "stopped", "info": ""}
        }
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统性能指标"""
        if self.psutil is None:
            # 返回模拟数据
            return {
                "cpu": {
                    "percent": 25,
                    "cores": 4,
                    "frequency": 2400,
                    "model": "模拟CPU"
                },
                "memory": {
                    "total": 8 * 1024 * 1024 * 1024,  # 8GB
                    "used": 4 * 1024 * 1024 * 1024,   # 4GB
                    "free": 4 * 1024 * 1024 * 1024,   # 4GB
                    "percent": 50
                },
                "network": {
                    "sent": 500000,
                    "received": 1500000,
                    "sentRate": 50000,
                    "receivedRate": 150000
                },
                "missing_psutil": True
            }
            
        # 使用psutil获取实际指标
        try:
            # CPU信息
            cpu_percent = self.psutil.cpu_percent(interval=0.5)
            cpu_count = self.psutil.cpu_count(logical=True)
            
            # 获取CPU频率
            try:
                cpu_freq = self.psutil.cpu_freq()
                cpu_frequency = cpu_freq.current if cpu_freq else 0
            except Exception:
                cpu_frequency = 0
            
            # 获取CPU型号
            cpu_model = "Unknown CPU"
            if sys.platform == "win32":
                import winreg
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
                    cpu_model = winreg.QueryValueEx(key, "ProcessorNameString")[0]
                except Exception:
                    pass
            
            # 内存信息
            mem = self.psutil.virtual_memory()
            
            # 网络信息
            net_io = self.psutil.net_io_counters()
            
            # 计算网络速率
            current_time = time.time()
            current_sent = net_io.bytes_sent
            current_recv = net_io.bytes_recv
            
            sent_rate = 0
            recv_rate = 0
            
            if "network" in self.last_metrics:
                last_time = self.last_metrics.get("time", current_time - 1)
                time_diff = current_time - last_time
                
                if time_diff > 0:
                    sent_rate = (current_sent - self.last_metrics["network"]["sent"]) / time_diff
                    recv_rate = (current_recv - self.last_metrics["network"]["received"]) / time_diff
            
            # 更新缓存
            self.last_metrics = {
                "time": current_time,
                "network": {
                    "sent": current_sent,
                    "received": current_recv
                }
            }
            
            # 返回结果
            return {
                "cpu": {
                    "percent": cpu_percent,
                    "cores": cpu_count,
                    "frequency": cpu_frequency,
                    "model": cpu_model
                },
                "memory": {
                    "total": mem.total,
                    "used": mem.used,
                    "free": mem.available,
                    "percent": mem.percent
                },
                "network": {
                    "sent": current_sent,
                    "received": current_recv,
                    "sentRate": sent_rate,
                    "receivedRate": recv_rate
                }
            }
            
        except Exception as e:
            logger.error(f"获取系统指标失败: {e}", exc_info=True)
            return {"error": str(e)}
    
    async def install_psutil(self) -> Dict[str, Any]:
        """尝试安装psutil"""
        if not self.missing_psutil:
            return {"success": True, "message": "psutil已安装"}
        
        logger.info("尝试安装psutil...")
        try:
            # 使用pip安装psutil
            import subprocess
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "psutil"],
                capture_output=True,
                text=True,
                check=True
            )
            
            # 尝试导入psutil
            import psutil
            self.psutil = psutil
            self.missing_psutil = False
            
            return {
                "success": True,
                "message": "psutil安装成功",
                "details": result.stdout
            }
        except Exception as e:
            logger.error(f"安装psutil失败: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"安装失败: {str(e)}"
            }

import psutil
import json
import sys
from typing import Dict, Any
import time

class SystemMonitor:
    @staticmethod
    def get_metrics() -> Dict[str, Any]:
        """获取系统性能指标"""
        try:
            # 添加短暂延迟以确保CPU百分比计算正确
            cpu_percent = psutil.cpu_percent(interval=0.5)
            cpu_freq = psutil.cpu_freq()
            freq_value = cpu_freq.current if cpu_freq else 0
            
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            net_io = psutil.net_io_counters()
            
            return {
                "cpu": {
                    "usage": round(cpu_percent, 1),
                    "cores": psutil.cpu_count(logical=True),
                    "frequency": round(freq_value, 2)
                },
                "memory": {
                    "total": mem.total,
                    "used": mem.used,
                    "free": mem.available,
                    "usage": round(mem.percent, 1)
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "usage": round(disk.percent, 1),
                    "type": "SSD" if SystemMonitor.is_ssd() else "HDD"
                },
                "network": {
                    "sent": net_io.bytes_sent,
                    "received": net_io.bytes_recv,
                }
            }
        except Exception as e:
            return {"error": True, "message": str(e)}

    @staticmethod
    def is_ssd() -> bool:
        """简单判断是否为SSD"""
        try:
            # 这是一个非常简化的检测，仅基于磁盘I/O速度
            # 更准确的检测需要操作系统特定的API
            disk = psutil.disk_io_counters(perdisk=False)
            return disk.read_time > 0 and disk.read_time < 100
        except:
            return False

if __name__ == "__main__":
    try:
        # 确保即使有错误也能返回JSON
        metrics = SystemMonitor.get_metrics()
        print(json.dumps(metrics))
        sys.stdout.flush()
    except Exception as e:
        # 确保错误信息也是有效的JSON
        print(json.dumps({"error": True, "message": str(e)}))
        sys.stdout.flush()
        sys.exit(1)
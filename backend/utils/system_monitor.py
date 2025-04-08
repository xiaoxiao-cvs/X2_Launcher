import json
import sys
import platform
import psutil
import time

def get_system_metrics():
    """获取系统性能指标"""
    try:
        # CPU信息
        cpu_percent = psutil.cpu_percent(interval=0.5)
        cpu_count = psutil.cpu_count(logical=True)
        cpu_freq = psutil.cpu_freq()
        
        cpu_info = {
            "usage": round(cpu_percent, 1),
            "cores": cpu_count,
            "frequency": cpu_freq.current if cpu_freq else 0
        }
        
        # 内存信息
        memory = psutil.virtual_memory()
        memory_info = {
            "total": memory.total,
            "used": memory.used, 
            "free": memory.available,
            "usage": round(memory.percent, 1)
        }
        
        # 网络信息
        net_io = psutil.net_io_counters()
        network_info = {
            "sent": net_io.bytes_sent,
            "received": net_io.bytes_recv
        }
        
        # 输出JSON格式结果
        metrics = {
            "cpu": cpu_info,
            "memory": memory_info,
            "network": network_info,
            "timestamp": time.time()
        }
        
        print(json.dumps(metrics))
        return 0
    except Exception as e:
        print(json.dumps({
            "error": True,
            "message": str(e)
        }))
        return 1

if __name__ == "__main__":
    sys.exit(get_system_metrics())
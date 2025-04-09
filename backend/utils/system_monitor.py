import sys
import json
import time
import os

# 尝试导入psutil，如果不存在则提供假数据
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("警告: psutil模块未安装，将使用模拟数据")

def get_system_info():
    """获取系统信息"""
    if not PSUTIL_AVAILABLE:
        # 如果psutil不可用，返回模拟数据
        return {
            "cpu": {
                "percent": 25,
                "cores": 4,
                "frequency": 2400
            },
            "memory": {
                "total": 8 * 1024 * 1024 * 1024,  # 8GB
                "used": 4 * 1024 * 1024 * 1024,   # 4GB
                "percent": 50
            },
            "disk": {
                "total": 500 * 1024 * 1024 * 1024,  # 500GB
                "used": 200 * 1024 * 1024 * 1024,   # 200GB
                "percent": 40
            },
            "network": {
                "sent": 0,
                "recv": 0
            },
            "missing_psutil": True
        }

    # 正常获取系统信息
    try:
        # CPU信息
        cpu_percent = psutil.cpu_percent(interval=0.5)
        cpu_count = psutil.cpu_count(logical=True)
        
        # 获取CPU频率
        try:
            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                cpu_frequency = cpu_freq.current  # MHz
            else:
                cpu_frequency = 0
        except (AttributeError, KeyError):
            cpu_frequency = 0
        
        # 尝试获取CPU温度（不是所有系统都支持）
        try:
            temps = psutil.sensors_temperatures()
            cpu_temp = next(iter(temps.values()))[0].current if temps else "N/A"
        except (AttributeError, KeyError, StopIteration):
            cpu_temp = "N/A"
        
        # 内存信息
        mem = psutil.virtual_memory()
        
        # 磁盘信息
        disk = psutil.disk_usage('/')
        
        # 网络信息
        net_io = psutil.net_io_counters()
        
        return {
            "cpu": {
                "percent": cpu_percent,
                "cores": cpu_count,
                "frequency": cpu_frequency
            },
            "memory": {
                "total": mem.total,
                "used": mem.used,
                "percent": mem.percent
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "percent": disk.percent
            },
            "network": {
                "sent": net_io.bytes_sent,
                "received": net_io.bytes_recv
            }
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    # 输出JSON格式的系统信息
    print(json.dumps(get_system_info()))
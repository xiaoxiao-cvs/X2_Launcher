import asyncio
import socket
import json
from pathlib import Path
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

def load_ports_config():
    """加载端口配置"""
    try:
        config_path = Path(__file__).parent.parent.parent / 'config.json'
        with open(config_path, 'r') as f:
            config = json.load(f)
            return config.get('ports', {'min': 11711, 'max': 11720})
    except Exception as e:
        XLogger.log(f"加载端口配置失败: {e}", "ERROR")
        return {'min': 11711, 'max': 11720}  # 默认值

def is_port_available(port: int) -> bool:
    """检查端口是否可用"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', port))
            return True
    except:
        return False

def find_available_port() -> int:
    """查找可用端口"""
    ports_config = load_ports_config()
    start_port = ports_config['min']
    end_port = ports_config['max']
    
    for port in range(start_port, end_port + 1):
        if is_port_available(port):
            XLogger.log(f"找到可用端口: {port}", "INFO")
            return port
            
    XLogger.log(f"在{start_port}-{end_port}范围内未找到可用端口", "ERROR")
    raise RuntimeError(f"无法在{start_port}-{end_port}范围内找到可用端口")

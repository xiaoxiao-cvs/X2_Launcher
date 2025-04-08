import socket
import json
from pathlib import Path

def load_config():
    config_path = Path(__file__).parent.parent.parent / 'config.json'
    with open(config_path, 'r') as f:
        return json.load(f)

def find_available_port():
    """自动寻找可用端口"""
    config = load_config()
    start_port = config['ports']['min']
    end_port = config['ports']['max']
    
    for port in range(start_port, end_port + 1):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"无法在{start_port}-{end_port}范围内找到可用端口")

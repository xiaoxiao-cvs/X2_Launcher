import os
import sys
import time
import json
import subprocess
import signal
import platform
import socket
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import psutil

from .logger import XLogger
from .process_manager import ProcessManager

class BotManager:
    """Bot管理器类，用于管理MaiBot及其依赖组件的生命周期"""
    
    def __init__(self):
        """初始化Bot管理器"""
        self.logger = XLogger
        self.process = ProcessManager()
        self.base_path = Path(__file__).parent.parent.parent
        
        # 进程映射
        self.processes = {
            'napcat': None,
            'nonebot': None, 
            'maibot': None
        }
        
        # 端口映射
        self.ports = {
            'napcat': 8095,
            'nonebot': 18002,
            'maibot': 8000
        }
    
    def set_ports(self, napcat_port: int = 8095, nonebot_port: int = 18002, maibot_port: int = 8000):
        """设置各组件的端口"""
        self.ports['napcat'] = napcat_port
        self.ports['nonebot'] = nonebot_port
        self.ports['maibot'] = maibot_port
    
    def start_napcat(self, instance_path: str) -> Tuple[bool, str]:
        """启动NapCat WebSocket服务器"""
        self.logger.log(f"尝试启动NapCat - 实例路径: {instance_path}")
        
        # 查找所有QQ配置
        napcat_path = Path(instance_path) / "napcat"
        config_dir = napcat_path / "versions/9.9.18-32793/resources/app/napcat/config"
        
        if not napcat_path.exists():
            return False, f"NapCat未安装: {napcat_path}"
        
        if not config_dir.exists():
            return False, f"NapCat配置目录不存在: {config_dir}"
        
        # 查找可用的配置文件
        napcat_configs = list(config_dir.glob("napcat_*.json"))
        onebot_configs = list(config_dir.glob("onebot11_*.json"))
        
        if not napcat_configs:
            return False, "未找到NapCat配置文件"
        
        if not onebot_configs:
            return False, "未找到OneBot配置文件"
        
        # 提取第一个配置中的QQ号
        qq_number = None
        for config in napcat_configs:
            qq_match = config.name.replace("napcat_", "").replace(".json", "")
            if qq_match.isdigit():
                qq_number = qq_match
                break
        
        if not qq_number:
            return False, "无法从配置中获取QQ号"
        
        # 启动NapCat
        exe_path = napcat_path / "NapCat QQ.exe"
        if not exe_path.exists():
            return False, f"NapCat执行文件不存在: {exe_path}"
        
        try:
            # 启动进程
            process = subprocess.Popen(
                [str(exe_path)],
                cwd=str(napcat_path),
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            
            self.processes['napcat'] = process
            self.logger.log(f"NapCat已启动，PID: {process.pid}, QQ: {qq_number}")
            
            # 检查端口是否可用（等待一段时间）
            time.sleep(2)
            if self.check_port_in_use(self.ports['napcat']):
                return True, f"NapCat已启动，QQ: {qq_number}"
            else:
                # 再等待一段时间
                time.sleep(3)
                if self.check_port_in_use(self.ports['napcat']):
                    return True, f"NapCat已启动，QQ: {qq_number}"
                else:
                    # 进程已启动但端口未开启，可能是启动中
                    return True, f"NapCat启动中，请稍后检查端口 {self.ports['napcat']}"
        
        except Exception as e:
            self.logger.log(f"启动NapCat失败: {e}", "ERROR")
            return False, f"启动NapCat失败: {e}"
    
    def start_nonebot(self, instance_path: str) -> Tuple[bool, str]:
        """启动NoneBot适配器"""
        self.logger.log(f"尝试启动NoneBot适配器 - 实例路径: {instance_path}")
        
        nonebot_path = Path(instance_path) / "nonebot-maibot-adapter"
        
        if not nonebot_path.exists():
            return False, f"NoneBot适配器未安装: {nonebot_path}"
        
        # 检查NapCat是否已启动
        if not self.is_service_running('napcat'):
            return False, "NapCat未启动，请先启动NapCat"
        
        try:
            # 创建或更新.env文件
            env_path = nonebot_path / ".env"
            env_content = f"""ENVIRONMENT=dev
DRIVER=~fastapi+websockets
PORT={self.ports['nonebot']}
HOST=0.0.0.0
ONEBOT_WS_URLS=["ws://127.0.0.1:{self.ports['napcat']}"]
"""
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write(env_content)
            
            # 使用nb run命令启动
            python_path = self.get_python_path(instance_path)
            
            # 构建命令
            cmd = [
                str(python_path),
                "-m",
                "nb", 
                "run", 
                "--reload"
            ]
            
            # 启动进程
            process = subprocess.Popen(
                cmd,
                cwd=str(nonebot_path),
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            
            self.processes['nonebot'] = process
            self.logger.log(f"NoneBot适配器已启动，PID: {process.pid}")
            
            # 检查端口是否可用（等待一段时间）
            time.sleep(2)
            if self.check_port_in_use(self.ports['nonebot']):
                return True, f"NoneBot适配器已启动，端口: {self.ports['nonebot']}"
            else:
                # 再等待一段时间
                time.sleep(3)
                if self.check_port_in_use(self.ports['nonebot']):
                    return True, f"NoneBot适配器已启动，端口: {self.ports['nonebot']}"
                else:
                    return True, f"NoneBot适配器启动中，请稍后检查端口 {self.ports['nonebot']}"
        
        except Exception as e:
            self.logger.log(f"启动NoneBot适配器失败: {e}", "ERROR")
            return False, f"启动NoneBot适配器失败: {e}"
    
    def start_maibot(self, instance_path: str) -> Tuple[bool, str]:
        """启动MaiBot主程序"""
        self.logger.log(f"尝试启动MaiBot - 实例路径: {instance_path}")
        
        maibot_path = Path(instance_path) / "MaiBot"
        
        if not maibot_path.exists():
            return False, f"MaiBot未安装: {maibot_path}"
        
        # 检查NoneBot是否已启动
        if not self.is_service_running('nonebot'):
            return False, "NoneBot适配器未启动，请先启动NoneBot适配器"
        
        # 检查配置文件
        config_path = maibot_path.parent / "config" / "bot_config.toml"
        if not config_path.exists():
            return False, f"MaiBot配置文件不存在: {config_path}"
        
        try:
            # 更新环境变量文件
            env_path = maibot_path / ".env"
            env_content = f"""ENVIRONMENT=dev
PORT={self.ports['maibot']}
"""
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write(env_content)
            
            # 获取Python路径
            python_path = self.get_python_path(instance_path)
            
            # 构建命令
            cmd = [
                str(python_path),
                "main.py"
            ]
            
            # 启动进程
            process = subprocess.Popen(
                cmd,
                cwd=str(maibot_path),
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            
            self.processes['maibot'] = process
            self.logger.log(f"MaiBot已启动，PID: {process.pid}")
            
            # 检查端口是否可用
            time.sleep(2)
            if self.check_port_in_use(self.ports['maibot']):
                return True, f"MaiBot已启动，端口: {self.ports['maibot']}"
            else:
                time.sleep(3)
                return True, f"MaiBot启动中，请稍后检查端口 {self.ports['maibot']}"
        
        except Exception as e:
            self.logger.log(f"启动MaiBot失败: {e}", "ERROR")
            return False, f"启动MaiBot失败: {e}"
    
    def stop_service(self, service_name: str) -> Tuple[bool, str]:
        """停止指定服务"""
        self.logger.log(f"尝试停止服务: {service_name}")
        
        process = self.processes.get(service_name)
        if not process:
            return True, f"{service_name}未在运行"
        
        try:
            # 尝试正常终止进程
            if platform.system() == "Windows":
                process.terminate()
            else:
                os.kill(process.pid, signal.SIGTERM)
            
            # 等待进程结束
            try:
                process.wait(timeout=5)
                self.processes[service_name] = None
                return True, f"{service_name}已停止"
            except subprocess.TimeoutExpired:
                # 如果超时，强制结束进程
                if platform.system() == "Windows":
                    process.kill()
                else:
                    os.kill(process.pid, signal.SIGKILL)
                
                self.processes[service_name] = None
                return True, f"{service_name}已强制停止"
        
        except Exception as e:
            self.logger.log(f"停止{service_name}失败: {e}", "ERROR")
            return False, f"停止{service_name}失败: {e}"
    
    def stop_all_services(self) -> Tuple[bool, str]:
        """停止所有服务"""
        self.logger.log("尝试停止所有服务")
        
        # 按照依赖关系的相反顺序停止服务
        services = ['maibot', 'nonebot', 'napcat']
        results = []
        
        for service in services:
            success, message = self.stop_service(service)
            results.append(f"{service}: {message}")
        
        return True, ", ".join(results)
    
    def get_service_status(self, instance_path: Optional[str] = None) -> Dict[str, str]:
        """获取所有服务的状态"""
        status = {}
        
        # 检查进程状态
        for service, process in self.processes.items():
            if not process:
                status[service] = 'stopped'
            else:
                try:
                    # 检查进程是否还在运行
                    if process.poll() is None:
                        # 进程在运行中，检查端口是否可用
                        if self.check_port_in_use(self.ports[service]):
                            status[service] = 'running'
                        else:
                            status[service] = 'error'
                    else:
                        # 进程已退出
                        status[service] = 'stopped'
                        self.processes[service] = None
                except Exception:
                    status[service] = 'unknown'
                    self.processes[service] = None
        
        # 对于未启动的服务，检查是否已安装
        if instance_path:
            if 'napcat' not in status or status['napcat'] == 'stopped':
                napcat_path = Path(instance_path) / "napcat" / "NapCat QQ.exe"
                status['napcat'] = 'stopped' if napcat_path.exists() else 'not_installed'
            
            if 'nonebot' not in status or status['nonebot'] == 'stopped':
                nonebot_path = Path(instance_path) / "nonebot-maibot-adapter"
                status['nonebot'] = 'stopped' if nonebot_path.exists() else 'not_installed'
            
            if 'maibot' not in status or status['maibot'] == 'stopped':
                maibot_path = Path(instance_path) / "MaiBot" / "main.py"
                status['maibot'] = 'stopped' if maibot_path.exists() else 'not_installed'
        
        return status
    
    def is_service_running(self, service_name: str) -> bool:
        """检查服务是否正在运行"""
        process = self.processes.get(service_name)
        if not process:
            return False
        
        try:
            # 检查进程是否还在运行
            if process.poll() is None:
                # 进程在运行中，检查端口是否可用
                return self.check_port_in_use(self.ports[service_name])
            else:
                # 进程已退出
                self.processes[service_name] = None
                return False
        except Exception:
            self.processes[service_name] = None
            return False
    
    def check_port_in_use(self, port: int) -> bool:
        """检查端口是否被占用"""
        try:
            # 检查本地端口是否被占用
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('127.0.0.1', port))
                return result == 0
        except Exception:
            return False
    
    def get_python_path(self, instance_path: str) -> Path:
        """获取Python路径，优先使用虚拟环境"""
        venv_python = Path(instance_path) / "venv" / "Scripts" / "python.exe"
        
        if venv_python.exists():
            return venv_python
        
        # 回退到系统Python
        return Path(sys.executable)

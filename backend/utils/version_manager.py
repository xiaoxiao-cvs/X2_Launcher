# -*- coding: utf-8 -*-
import os
import sys
import logging
import asyncio
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from pathlib import Path
from typing import List, Optional, Dict, Any
from packaging import version

from .github_client import GitHubClient
from .process_manager import ProcessManager
from .settings import AppConfig as Settings
from .logger import XLogger  # 修复这里的导入
from .errors import DeploymentError, GitHubAPIError, ProcessError, BotError, DependencyError

class VersionController:
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.settings = Settings()
        self.github = GitHubClient(self.config.get('github_token'))
        self.process = ProcessManager()
        
        # 初始化路径
        self.base_path = Path(__file__).parent.parent
        self.repo_url = self.settings.get("deployment", "repo_url")
        self.local_path = self.settings.get("deployment", "install_path")
        
        # 修复这一行，移除 fallback 参数
        install_path = self.settings.get("deployment", "install_path")
        self.instances_dir = install_path if install_path else os.path.join(self.base_path, "maibot_versions")
        
        # 确保实例目录存在
        if not os.path.exists(self.instances_dir):
            os.makedirs(self.instances_dir)
        
        # 监控实例状态
        self.running_instances = {}
        self._instance_logs = {}
        
        # 确保目录存在
        if not os.path.exists(self.local_path):
            os.makedirs(self.local_path)
            
        self.bot_process: Optional[subprocess.Popen] = None
        self.log_callback = None
        self.logger = XLogger
        self._version_cache = {}
        self.venv_cache = {}

    def set_log_callback(self, callback):
        """设置日志回调函数"""
        self.logger.add_callback(callback)

    def _log(self, message, level="INFO"):
        """统一的日志处理"""
        self.logger.log(message, level)

    async def async_get_versions(self) -> List[str]:
        """异步获取所有版本"""
        try:
            releases, branches = await asyncio.gather(
                self.github.async_get_releases(self.repo_url),
                self.github.async_get_branches(self.repo_url)
            )
            return self._process_versions(releases, branches)
        except Exception as e:
            self._log(f"版本获取失败: {str(e)}", "ERROR")
            return ["NaN"]

    def get_versions(self) -> List[str]:
        """获取所有版本"""
        try:
            releases = self.github.get_releases(self.repo_url)
            branches = self.github.get_branches(self.repo_url)
            return self._process_versions(releases, branches)
        except GitHubAPIError as e:
            self.logger.log(f"API访问失败: {e}", "ERROR")
            return ["NaN"]
        except Exception as e:
            self.logger.log(f"版本获取失败: {e}", "ERROR")
            return ["NaN"]

    def _process_versions(self, releases: List[Dict[str, Any]], branches: List[Dict[str, Any]]) -> List[str]:
        """提取出来的版本处理逻辑"""
        version_list = []
        
        version_list.extend(
            f"Release {r['tag_name']}" 
            for r in releases 
            if not r['prerelease']
        )
        
        version_list.extend(
            f"Branch {b['name']}" 
            for b in branches
        )
        
        self._update_version_cache(releases, branches)
        
        return sorted(
            version_list,
            key=self._version_key,
            reverse=True
        ) or ["NaN"]

    def _update_version_cache(self, releases: List[Dict[str, Any]], branches: List[Dict[str, Any]]) -> None:
        """更新版本缓存"""
        self._version_cache.clear()
        
        for release in releases:
            if not release['prerelease']:
                key = f"Release {release['tag_name']}"
                self._version_cache[key] = release
        
        for branch in branches:
            key = f"Branch {branch['name']}"
            self._version_cache[key] = branch

    @staticmethod
    def _version_key(version_str: str) -> version.Version:
        """专业版本排序"""
        try:
            version_part = version_str.split()[-1].lstrip('v')
            return version.parse(version_part)
        except:
            return version.parse("0.0.0")

    def get_version_info(self, version_str: str) -> Optional[Dict]:
        """获取指定版本的详细信息"""
        return self._version_cache.get(version_str)

    def clone_version(self, version: str) -> bool:
        """克隆版本并设置环境"""
        try:
            target_path = os.path.join(self.local_path, version)
            success = False
            
            self._log(f"开始部署版本: {version}")
            self._log(f"目标路径: {target_path}")
            
            if os.path.exists(target_path):
                self._log("检测到现有仓库，尝试更新...")
                success = self._update_repository(target_path)
            else:
                self._log("未找到现有仓库，开始克隆...")
                success = self._clone_repository(version, target_path)
            
            if success:
                self._log("代码操作成功，准备配置环境...")
                return self._setup_virtual_env(target_path, version)
            else:
                self._log("代码操作失败，跳过环境配置", "ERROR")
                return False
                
        except Exception as e:
            self._log(f"部署失败: {str(e)}", "ERROR")
            return False

    def _clone_repository(self, version: str, target_path: str) -> bool:
        """克隆仓库"""
        try:
            branch_name = version.split(" ")[-1]
            
            self._log(f"正在克隆分支/标签: {branch_name}")
            for output in self.process.run_command(
                ["git", "clone", "-b", branch_name, "--depth", "1", self.repo_url, target_path],
                realtime_output=True
            ):
                self._log(output)
            
            if os.path.exists(target_path):
                self._log(f"仓库克隆成功到: {target_path}")
                return True
            else:
                self._log("仓库克隆失败：目标目录未创建", "ERROR")
                return False
                
        except Exception as e:
            self._log(f"克隆仓库失败: {str(e)}", "ERROR")
            return False

    def _update_repository(self, target_path: str) -> bool:
        """更新仓库"""
        try:
            self._log(f"正在更新仓库: {target_path}")
            for output in self.process.run_command(
                ["git", "pull"],
                cwd=target_path,
                realtime_output=True
            ):
                self._log(output)
            return True
                
        except Exception as e:
            self._log(f"更新仓库失败: {str(e)}", "ERROR")
            return False

    def _setup_virtual_env(self, target_path: str, version: str) -> bool:
        try:
            venv_path = os.path.join(target_path, 'venv')
            requirements_path = os.path.join(target_path, "requirements.txt")
            
            python_path = os.path.join(
                venv_path, 
                'Scripts' if os.name == 'nt' else 'bin',
                'python' + ('.exe' if os.name == 'nt' else '')
            )
            pip_path = os.path.join(
                venv_path,
                'Scripts' if os.name == 'nt' else 'bin',
                'pip' + ('.exe' if os.name == 'nt' else '')
            )
            
            # 1. 创建虚拟环境
            if not os.path.exists(venv_path):
                self._log("正在创建虚拟环境...")
                for output in self.process.run_command(
                    [sys.executable, "-m", "venv", venv_path],
                    realtime_output=True
                ):
                    self._log(output)
            
            # 2. 配置pip源
            self._log("正在配置pip源...")
            config_cmd = [
                pip_path, "config", "set", 
                "global.index-url", 
                "https://pypi.tuna.tsinghua.edu.cn/simple"
            ]
            for output in self.process.run_command(config_cmd, realtime_output=True):
                self._log(output)
            
            # 3. 升级pip和setuptools
            self._log("正在更新基础工具...")
            for output in self.process.run_command(
                [python_path, "-m", "pip", "install", "--upgrade", "pip==24.0", "setuptools==68.0.0"],
                realtime_output=True
            ):
                self._log(output)
            
            # 4. 安装项目依赖
            if os.path.exists(requirements_path):
                self._log("正在安装项目依赖...")
                self._install_dependencies(python_path, requirements_path)
            else:
                self._log("未找到requirements.txt，跳过依赖安装", "WARNING")
            
            self.venv_cache[version] = venv_path
            return True
            
        except Exception as e:
            self._log(f"虚拟环境设置失败: {e}", "ERROR")
            return False

    def _install_dependencies(self, python_path: str, requirements_path: str):
        """安装依赖的内部方法"""
        # 使用国内镜像源
        mirrors = [
            "https://pypi.tuna.tsinghua.edu.cn/simple",
            "https://mirrors.aliyun.com/pypi/simple/",
            "https://pypi.mirrors.ustc.edu.cn/simple/"
        ]
        
        for mirror in mirrors:
            try:
                self._log(f"尝试使用镜像源: {mirror}")
                self._log(f"开始安装依赖，路径: {requirements_path}")
                for output in self.process.run_command(
                    [
                        python_path, "-m", "pip", "install",
                        "-r", requirements_path,
                        "-i", mirror,
                        "--trusted-host", mirror.split('/')[2],
                        "--timeout", "60",
                        "--retries", "3",
                        "-v",
                        "--progress-bar=on"
                    ],
                    realtime_output=True
                ):
                    if output.strip():
                        self._log(output)
                self._log("依赖安装成功")
                # 安装完成后解锁按钮
                self._unlock_buttons()
                return  # 如果成功安装，直接返回
            except Exception as e:
                self._log(f"使用镜像 {mirror} 安装失败: {str(e)}", "WARNING")
                continue
        
        # 如果所有镜像都失败，尝试使用默认源
        self._log("所有镜像安装失败，尝试使用默认源")
        try:
            for output in self.process.run_command(
                [
                    python_path, "-m", "pip", "install",
                    "-r", requirements_path,
                    "--timeout", "60",
                    "--retries", "3",
                    "-v",
                    "--progress-bar=on"
                ],
                realtime_output=True
            ):
                if output.strip():
                    self._log(output)
            self._log("依赖安装成功")
            # 安装完成后解锁按钮
            self._unlock_buttons()
        except Exception as e:
            self._log(f"使用默认源安装失败: {str(e)}", "ERROR")

    def _unlock_buttons(self):
        """解锁按钮的内部方法"""
        # 假设有两个按钮需要解锁，这里调用UI层的方法
        if hasattr(self, 'ui'):
            self.ui.unlock_buttons()

    def start_bot(self, version: str) -> bool:
        """使用虚拟环境启动机器人"""
        try:
            # 停止当前运行的机器人
            if self.bot_process:
                self.stop_bot()
            
            # 获取版本目录的完整路径
            version_dir = os.path.join(self.instances_dir, version)
            bot_path = os.path.join(version_dir, "bot.py")
            
            if not os.path.exists(bot_path):
                raise FileNotFoundError(f"未找到机器人文件: {bot_path}")
            
            python_path = os.path.join(
                self.venv_cache.get(version, os.path.join(version_dir, 'venv')),
                'Scripts' if os.name == 'nt' else 'bin',
                'python' + ('.exe' if os.name == 'nt' else '')
            )
                
            self._log(f"正在启动机器人，使用Python: {python_path}")
            self._log(f"运行目录: {version_dir}")
            self._log(f"Bot文件: {bot_path}")
            
            # 创建进程，并将输出重定向到回调函数
            self.bot_process = self.process.run_with_callback(
                [python_path, "bot.py"],
                cwd=version_dir,
                callback=lambda line: self._process_bot_output(line, version)
            )
            
            # 记录运行状态
            self.running_instances[version] = {
                'process': self.bot_process,
                'start_time': self._format_timestamp(time.time())
            }
            
            return True
            
        except Exception as e:
            self._log(f"启动失败: {str(e)}", "ERROR")
            return False

    def stop_bot(self) -> bool:
        """停止机器人"""
        if self.bot_process:
            return self.process.kill_process_tree(self.bot_process.pid)
        return True

    def get_installed_instances(self) -> List[Dict[str, Any]]:
        """获取所有已安装的实例"""
        instances = []
        
        try:
            if not os.path.exists(self.instances_dir):
                return []
                
            for dirname in os.listdir(self.instances_dir):
                path = os.path.join(self.instances_dir, dirname)
                if os.path.isdir(path):
                    # 检查是否是有效的bot目录
                    if os.path.exists(os.path.join(path, "bot.py")):
                        # 获取创建时间
                        created_time = os.path.getctime(path)
                        formatted_time = self._format_timestamp(created_time)
                        
                        # 确定实例运行状态
                        status = "running" if dirname in self.running_instances else "stopped"
                        
                        instances.append({
                            "name": dirname,
                            "path": path,
                            "installedAt": formatted_time,
                            "status": status
                        })
        except Exception as e:
            self._log(f"获取已安装实例失败: {e}", "ERROR")
        
        return instances
    
    def get_instance_logs(self, instance_name: str) -> List[Dict[str, Any]]:
        """获取特定实例的日志"""
        if instance_name not in self._instance_logs:
            return []
        return self._instance_logs[instance_name]
    
    def _format_timestamp(self, timestamp) -> str:
        """格式化时间戳为人类可读形式"""
        from datetime import datetime
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    def register_instance_log(self, instance_name: str, log_entry: Dict[str, Any]) -> None:
        """注册实例日志"""
        if instance_name not in self._instance_logs:
            self._instance_logs[instance_name] = []
            
        # 限制日志条数，防止内存溢出
        if len(self._instance_logs[instance_name]) > 1000:
            self._instance_logs[instance_name] = self._instance_logs[instance_name][-900:]
            
        self._instance_logs[instance_name].append(log_entry)
    
    async def get_system_logs(self) -> List[Dict[str, Any]]:
        """获取系统日志"""
        return self.logger.get_log_history()
    
    def delete_instance(self, instance_name: str) -> bool:
        """删除指定实例"""
        try:
            # 确保实例已停止
            if instance_name in self.running_instances:
                self.stop_bot()
                
            instance_path = os.path.join(self.instances_dir, instance_name)
            if os.path.exists(instance_path):
                import shutil
                shutil.rmtree(instance_path)
                
                # 清理相关缓存
                if instance_name in self.venv_cache:
                    del self.venv_cache[instance_name]
                if instance_name in self._instance_logs:
                    del self._instance_logs[instance_name]
                if instance_name in self.running_instances:
                    del self.running_instances[instance_name]
                    
                return True
            return False
        except Exception as e:
            self._log(f"删除实例 {instance_name} 失败: {e}", "ERROR")
            return False
    
    def open_folder(self, path: str) -> bool:
        """打开文件夹"""
        try:
            if not os.path.exists(path):
                self._log(f"路径不存在: {path}", "ERROR")
                return False
                
            if sys.platform == 'win32':
                os.startfile(path)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', path])
            else:  # linux或其他系统
                subprocess.Popen(['xdg-open', path])
                
            return True
        except Exception as e:
            self._log(f"打开文件夹失败: {e}", "ERROR")
            return False

    def update_instance(self, instance_name: str) -> bool:
        """更新指定实例"""
        instance_path = os.path.join(self.instances_dir, instance_name)
        
        # 确保实例已停止
        if instance_name in self.running_instances:
            self.stop_bot()
            
        return self._update_repository(instance_path)

    def _process_bot_output(self, line: str, instance_name: str) -> None:
        """处理Bot进程输出"""
        if not line:
            return
            
        # 尝试解析日志级别，默认为INFO
        level = "INFO"
        if "[ERROR]" in line or "Error:" in line:
            level = "ERROR"
        elif "[WARNING]" in line or "Warning:" in line:
            level = "WARNING"
        
        # 创建日志条目
        entry = {
            "time": self._format_timestamp(time.time()),
            "message": line.strip(),
            "type": level,
            "source": instance_name
        }
        
        # 注册日志
        self.register_instance_log(instance_name, entry)
        
        # 触发WebSocket通知，如果存在
        self._notify_log_subscribers(entry)
    
    def _notify_log_subscribers(self, log_entry: Dict[str, Any]) -> None:
        """通知日志订阅者"""
        # 这里将在WebSocket实现时完成
        pass

    def run_with_callback(self, cmd, cwd=None, callback=None, shell=False):
        """
        运行进程并将输出发送到回调函数
        """
        # 确保过程允许交互输入
        process = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,  # 允许标准输入
            shell=shell,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # 创建线程来读取输出并发送到回调
        def reader_thread():
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if callback and line:
                    callback(line.rstrip())
        
        threading.Thread(target=reader_thread, daemon=True).start()
        return process
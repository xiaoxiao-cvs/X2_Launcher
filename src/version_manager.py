# -*- coding: utf-8 -*-
import os
import sys
import logging
import asyncio
import subprocess
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from pathlib import Path
from typing import List, Optional, Dict, Any
from packaging import version

from .github_client import GitHubClient
from .process_manager import ProcessManager
from .settings import AppConfig as Settings
from .logger import logger
from .errors import DeploymentError, GitHubAPIError, ProcessError, BotError, DependencyError

class VersionController:
    def __init__(self, config=None):
        self.config = config
        self.settings = Settings()
        self.github = GitHubClient(config.config.get('github_token') if config else None)
        self.process = ProcessManager()
        
        # 初始化路径
        self.base_path = Path(__file__).parent.parent
        self.repo_url = self.settings.get("deployment", "repo_url")
        self.local_path = self.settings.get("deployment", "install_path")
        
        # 确保目录存在
        if not os.path.exists(self.local_path):
            os.makedirs(self.local_path)
            
        self.bot_process: Optional[subprocess.Popen] = None
        self.log_callback = None
        self.logger = logger
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
        """设置虚拟环境"""
        try:
            venv_path = os.path.join(target_path, 'venv')
            requirements_path = os.path.join(target_path, "requirements.txt")
            
            python_path = os.path.join(
                venv_path, 
                'Scripts' if os.name == 'nt' else 'bin',
                'python' + ('.exe' if os.name == 'nt' else '')
            )
            
            # 1. 创建虚拟环境
            if not os.path.exists(venv_path):
                self._log("正在创建虚拟环境...")
                for output in self.process.run_command(
                    [sys.executable, "-m", "venv", venv_path],
                    realtime_output=True
                ):
                    self._log(output)
            
            # 2. 升级pip和setuptools到兼容版本
            self._log("正在安装基础工具...")
            base_packages = [
                "pip==24.0",  # 使用稳定版本
                "setuptools==68.0.0"  # 兼容性较好的版本
            ]
            for output in self.process.run_command(
                [python_path, "-m", "pip", "install"] + base_packages,
                realtime_output=True
            ):
                self._log(output)
            
            # 3. 安装依赖(带重试机制)
            if os.path.exists(requirements_path):
                self._log("正在安装依赖(最多重试3次)...")
                max_retries = 3
                retry_count = 0
                success = False
                
                while not success and retry_count < max_retries:
                    try:
                        retry_count += 1
                        self._log(f"尝试第{retry_count}次安装...")
                        
                        # 使用稳定的镜像源组合
                        mirrors = [
                            "https://pypi.tuna.tsinghua.edu.cn/simple",
                            "https://mirrors.aliyun.com/pypi/simple",
                            "https://pypi.org/simple"
                        ]
                        current_mirror = mirrors[retry_count % len(mirrors)]
                        
                        # 添加超时和重试参数
                        cmd = [
                            python_path, "-m", "pip", "install",
                            "-r", requirements_path,
                            "-i", current_mirror,
                            "--timeout", "60",
                            "--retries", "3",
                            "--progress-bar", "on"
                        ]
                        
                        for output in self.process.run_command(cmd, realtime_output=True):
                            self._log(output)
                        
                        success = True
                        self._log("依赖安装成功")
                        
                    except Exception as e:
                        self._log(f"第{retry_count}次安装失败: {str(e)}", "WARNING")
                        if retry_count == max_retries:
                            self._log("达到最大重试次数，依赖安装失败", "ERROR")
                            return False
                        time.sleep(5)  # 等待5秒后重试
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
            "https://mirrors.aliyun.com/pypi/simple/",
            "https://pypi.tuna.tsinghua.edu.cn/simple/",
            "https://pypi.mirrors.ustc.edu.cn/simple/"
        ]
        
        for mirror in mirrors:
            try:
                self._log(f"尝试使用镜像源: {mirror}")
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
                return  # 如果成功安装，直接返回
            except Exception as e:
                self._log(f"使用镜像 {mirror} 安装失败: {e}", "WARNING")
                continue
        
        # 如果所有镜像都失败，尝试使用默认源
        self._log("所有镜像安装失败，尝试使用默认源")
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

    def start_bot(self, version: str) -> bool:
        """使用虚拟环境启动机器人"""
        try:
            if self.bot_process:
                self.stop_bot()
            
            bot_path = os.path.join(self.local_path, version)
            if not os.path.exists(os.path.join(bot_path, "bot.py")):
                raise FileNotFoundError("bot.py not found")
            
            python_path = os.path.join(
                self.venv_cache.get(version, os.path.join(bot_path, 'venv')),
                'Scripts' if os.name == 'nt' else 'bin',
                'python' + ('.exe' if os.name == 'nt' else '')
            )
                
            self._log(f"正在启动机器人，使用Python: {python_path}")
            self.bot_process = subprocess.Popen(
                [python_path, "bot.py"],
                cwd=bot_path,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            return True
        except Exception as e:
            self._log(f"启动失败: {str(e)}", "ERROR")
            return False

    def stop_bot(self) -> bool:
        """停止机器人"""
        if self.bot_process:
            return self.process.kill_process_tree(self.bot_process.pid)
        return True
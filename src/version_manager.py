# -*- coding: utf-8 -*-
import os
import sys
import logging
import asyncio
import subprocess  # 添加缺失的导入
from pathlib import Path
from typing import List, Optional, Dict, Any  # 添加Dict类型导入
from packaging import version

from .github_client import GitHubClient
from .process_manager import ProcessManager
from .settings import AppConfig as Settings  # 更新为新的配置类
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
        self._version_cache = {}  # 添加版本缓存
        self.venv_cache = {}  # 添加虚拟环境缓存

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
        
        # 处理发行版
        version_list.extend(
            f"Release {r['tag_name']}" 
            for r in releases 
            if not r['prerelease']
        )
        
        # 处理分支
        version_list.extend(
            f"Branch {b['name']}" 
            for b in branches
        )
        
        # 缓存版本信息
        self._update_version_cache(releases, branches)
        
        return sorted(
            version_list,
            key=self._version_key,
            reverse=True
        ) or ["NaN"]

    def _update_version_cache(self, releases: List[Dict[str, Any]], branches: List[Dict[str, Any]]) -> None:
        """更新版本缓存"""
        self._version_cache.clear()
        
        # 缓存发行版
        for release in releases:
            if not release['prerelease']:
                key = f"Release {release['tag_name']}"
                self._version_cache[key] = release
        
        # 缓存分支
        for branch in branches:
            key = f"Branch {branch['name']}"
            self._version_cache[key] = branch

    @staticmethod
    def _version_key(version_str: str) -> version.Version:
        """专业版本排序"""
        try:
            # 提取版本号并解析
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
            
            # 1. 首先执行Git操作
            if os.path.exists(target_path):
                self._log("正在更新仓库...")
                success = self._update_repository(target_path)
            else:
                self._log("正在克隆仓库...")
                success = self._clone_repository(version, target_path)
            
            # 2. 只有在Git操作成功后才创建虚拟环境
            if success:
                self._log("代码更新完成，准备配置环境...")
                return self._setup_virtual_env(target_path, version)
            else:
                self._log("代码获取失败，跳过环境配置", "ERROR")
                return False
                
        except Exception as e:
            self._log(f"部署失败: {str(e)}", "ERROR")
            return False

    def _clone_repository(self, version: str, target_path: str) -> bool:
        """克隆仓库"""
        try:
            # 提取真实的分支/标签名（移除"Release"或"Branch"前缀）
            branch_name = version.split(" ")[-1]
            
            # 执行git clone命令
            for output in self.process.run_command(
                ["git", "clone", "-b", branch_name, "--depth", "1", self.repo_url, target_path],
                realtime_output=True
            ):
                self._log(output)
            
            # 检查目标目录是否存在
            if os.path.exists(target_path) and os.path.isdir(target_path):
                self._log("仓库克隆成功")
                return True
            else:
                self._log("仓库克隆失败：目标目录不存在", "ERROR")
                return False
                
        except Exception as e:
            self._log(f"克隆仓库失败: {str(e)}", "ERROR")
            return False

    def _update_repository(self, target_path: str) -> bool:
        """更新仓库"""
        try:
            # 执行git pull命令
            for output in self.process.run_command(
                ["git", "pull"],
                cwd=target_path,
                realtime_output=True
            ):
                self._log(output)
            
            # 只要git pull命令成功执行就返回True
            return True
                
        except Exception as e:
            self._log(f"更新仓库失败: {str(e)}", "ERROR")
            return False

    def _setup_virtual_env(self, target_path: str, version: str) -> bool:
        """设置虚拟环境"""
        try:
            venv_path = os.path.join(target_path, 'venv')
            requirements_path = os.path.join(target_path, "requirements.txt")
            
            # 获取虚拟环境中的Python路径
            python_path = os.path.join(
                venv_path, 
                'Scripts' if os.name == 'nt' else 'bin',
                'python' + ('.exe' if os.name == 'nt' else '')
            )
            
            # 如果虚拟环境不存在,创建它
            if not os.path.exists(venv_path):
                self._log("创建虚拟环境...")
                for output in self.process.run_command(
                    [sys.executable, "-m", "venv", venv_path],
                    realtime_output=True
                ):
                    self._log(output)
            
            # 升级pip并实时显示输出
            self._log("升级pip...")
            for output in self.process.run_command(
                [python_path, "-m", "pip", "install", "--upgrade", "pip"],
                realtime_output=True
            ):
                self._log(output)
            
            # 安装依赖并实时显示输出
            if os.path.exists(requirements_path):
                self._log("安装依赖...")
                # 增加pip命令的详细输出参数
                for output in self.process.run_command(
                    [python_path, "-m", "pip", "install", "-r", requirements_path, "-v"],
                    realtime_output=True
                ):
                    if output.strip():  # 只输出非空行
                        self._log(output)
            
            # 缓存虚拟环境路径
            self.venv_cache[version] = venv_path
            return True
            
        except Exception as e:
            self._log(f"虚拟环境设置失败: {e}", "ERROR")
            return False

    def start_bot(self, version: str) -> bool:
        """使用虚拟环境启动机器人"""
        try:
            if self.bot_process:
                self.stop_bot()
            
            bot_path = os.path.join(self.local_path, version)
            if not os.path.exists(os.path.join(bot_path, "bot.py")):
                raise FileNotFoundError("bot.py not found")
            
            # 使用虚拟环境的Python
            python_path = os.path.join(
                self.venv_cache.get(version, os.path.join(bot_path, 'venv')),
                'Scripts' if os.name == 'nt' else 'bin',
                'python' + ('.exe' if os.name == 'nt' else '')
            )
                
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
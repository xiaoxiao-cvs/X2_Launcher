# -*- coding: utf-8 -*-
import subprocess
import os
import sys
import logging
import signal
import psutil
from typing import List, Optional
from tkinter import messagebox
from pathlib import Path
import requests

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.settings import Settings  # 修改导入路径

class VersionController:
    def __init__(self, config=None):
        self.config = config
        self.base_path = Path(__file__).parent.parent
        self.bot_path = self.base_path / "bot"
        self.settings = Settings()
        self.repo_url = self.settings.get("deployment", "repo_url")
        self.local_path = self.settings.get("deployment", "install_path")
        # 修改资源文件路径处理
        self.exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        python_version = self.settings.get("deployment", "python_version")
        self.python_installer = f"python-{python_version}-amd64.exe"
        self.python_path = os.path.join(self.exe_dir, self.python_installer)
        self.log_callback = None  # 添加日志回调
        self.github_token = self.config.config.get("github_token", None)  # 从配置中获取 GitHub Token
        
        # 确保目录存在
        if not os.path.exists(self.local_path):
            os.makedirs(self.local_path)
        
        self.bot_process: Optional[subprocess.Popen] = None
        self._setup_logging()

    def set_log_callback(self, callback):
        """设置日志回调函数"""
        self.log_callback = callback

    def _log(self, message, level="INFO"):
        """统一的日志处理"""
        logging.log(getattr(logging, level), message)
        if self.log_callback:
            self.log_callback(message, level)

    def _setup_logging(self):
        logging.basicConfig(
            filename='deploy.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def _get_headers(self):
        """生成请求头，支持 GitHub Token"""
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'X-Deploy-Station'
        }
        if self.github_token:
            headers['Authorization'] = f"token {self.github_token}"
        return headers

    def _check_repository(self) -> bool:
        """检查仓库是否存在且可访问"""
        try:
            # 修复仓库路径解析
            repo_path = self.repo_url.rstrip('/').replace('.git', '').split('github.com/')[-1]
            api_url = f"https://api.github.com/repos/{repo_path}"
            
            headers = self._get_headers()  # 使用统一的 headers 方法
            
            response = requests.get(api_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            repo_info = response.json()
            logging.info(f"仓库信息: {repo_info.get('full_name')}, 默认分支: {repo_info.get('default_branch')}")
            return True
            
        except requests.RequestException as e:
            logging.error(f"仓库检查失败: {e}")
            return False

    def get_versions(self) -> List[str]:
        """从GitHub获取发行版列表（包含分支）"""
        from urllib.parse import urlparse
        from packaging import version
        
        try:
            # 修复仓库路径解析
            repo_path = self.repo_url.rstrip('/').replace('.git', '').split('github.com/')[-1]
            
            # 获取发行版（带分页支持）
            releases = []
            page = 1
            while True:
                api_url = f"https://api.github.com/repos/{repo_path}/releases?page={page}&per_page=100"
                headers = self._get_headers()  # 使用统一的 headers 方法
                
                response = requests.get(api_url, headers=headers, timeout=15)
                response.raise_for_status()
                
                page_releases = response.json()
                if not page_releases:
                    break
                    
                releases.extend(page_releases)
                page += 1

            # 获取分支列表
            branches_url = f"https://api.github.com/repos/{repo_path}/branches"
            branches_response = requests.get(branches_url, headers=headers, timeout=15)
            branches = branches_response.json() if branches_response.status_code == 200 else []

            # 处理发行版数据
            version_list = []
            try:
                for release in releases:
                    # 过滤预发布版本
                    if not release['prerelease']:
                        version_list.append({
                            'type': 'release',
                            'name': f"Release {release['tag_name']}",
                            'value': release['tag_name']
                        })
            except KeyError as e:
                logging.error(f"发行版数据解析异常: {e}")

            # 处理分支数据
            try:
                for branch in branches:
                    version_list.append({
                        'type': 'branch',
                        'name': f"Branch {branch['name']}",
                        'value': branch['name']
                    })
            except KeyError as e:
                logging.error(f"分支数据解析异常: {e}")

            # 专业版本排序
            def sort_key(item):
                try:
                    return version.parse(item['value'].lstrip('v'))
                except:
                    return version.parse("0.0.0")
                    
            return sorted(
                [item['value'] for item in version_list],
                key=sort_key,
                reverse=True
            ) or ["NaN"]

        except requests.RequestException as e:
            logging.error(f"API请求失败: {e}")
            messagebox.showwarning("连接超时", "无法连接到GitHub服务器，请检查网络连接")
            return ["NaN"]
        except Exception as e:
            logging.error(f"版本获取失败: {str(e)}", exc_info=True)
            return ["NaN"]

    def clone_version(self, version: str) -> bool:
        try:
            target_path = os.path.join(self.local_path, version)
            if os.path.exists(target_path):
                self._log("正在更新仓库...")
                process = subprocess.Popen(
                    ["git", "pull"],
                    cwd=target_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
            else:
                self._log("正在克隆仓库...")
                os.makedirs(target_path)
                process = subprocess.Popen(
                    ["git", "clone", "-b", version, "--depth", "1", self.repo_url, target_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )

            # 实时输出日志
            while True:
                output = process.stdout.readline()
                error = process.stderr.readline()
                
                if output:
                    self._log(output.strip())
                if error:
                    self._log(error.strip(), "ERROR")
                    
                if process.poll() is not None:
                    break

            if process.returncode == 0:
                self._log("代码更新完成，正在安装依赖...")
                
                # 安装依赖
                requirements_path = os.path.join(target_path, "requirements.txt")
                if os.path.exists(requirements_path):
                    pip_process = subprocess.Popen(
                        [sys.executable, "-m", "pip", "install", "-r", requirements_path],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                    )
                    
                    # 实时输出pip安装日志
                    while True:
                        output = pip_process.stdout.readline()
                        error = pip_process.stderr.readline()
                        
                        if output:
                            self._log(output.strip())
                        if error:
                            self._log(error.strip(), "WARNING")
                            
                        if pip_process.poll() is not None:
                            break
                    
                    if pip_process.returncode == 0:
                        self._log("依赖安装完成")
                        return True
                    else:
                        raise Exception("依赖安装失败")
                return True
            else:
                raise Exception("代码更新/克隆失败")
                
        except Exception as e:
            self._log(f"部署失败: {str(e)}", "ERROR")
            return False

    def install_python(self) -> bool:
        try:
            if os.path.exists(self.python_path):
                print(f"正在安装Python: {self.python_path}")
                subprocess.run(
                    [self.python_path, "/quiet", "InstallAllUsers=1", "PrependPath=1"],
                    check=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                return True
            else:
                error_msg = f"Python安装包不存在: {self.python_path}"
                print(error_msg)
                messagebox.showerror("错误", error_msg)
                return False
        except Exception as e:
            error_msg = f"Python安装失败: {str(e)}"
            print(error_msg)
            messagebox.showerror("错误", error_msg)
            return False

    def start_bot(self, version: str) -> bool:
        try:
            if self.bot_process:
                self.stop_bot()
            
            bot_path = os.path.join(self.local_path, version)
            if not os.path.exists(os.path.join(bot_path, "bot.py")):
                raise FileNotFoundError("bot.py not found")
                
            self.bot_process = subprocess.Popen(
                [sys.executable, "bot.py"],
                cwd=bot_path,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            return True
        except Exception as e:
            logging.error(f"启动机器人失败: {e}")
            return False

    def stop_bot(self) -> bool:
        try:
            if self.bot_process:
                if os.name == 'nt':
                    self._kill_process_tree(self.bot_process.pid)
                else:
                    os.killpg(os.getpgid(self.bot_process.pid), signal.SIGTERM)
                self.bot_process = None
            return True
        except Exception as e:
            logging.error(f"停止机器人失败: {e}")
            return False

    def _kill_process_tree(self, pid):
        try:
            parent = psutil.Process(pid)
            for child in parent.children(recursive=True):
                child.kill()
            parent.kill()
        except psutil.NoSuchProcess:
            pass
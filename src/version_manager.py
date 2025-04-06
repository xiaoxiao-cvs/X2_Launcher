# -*- coding: utf-8 -*-
import subprocess
import os
from typing import List
from tkinter import messagebox

class VersionController:
    def __init__(self):
        self.repo_url = "https://github.com/MaiM-with-u/MaiBot.git"
        self.local_path = "maibot_versions"
        self.python_dir = "resources"
        self.python_installer = "python-3.13.0-amd64.exe"
        self.python_path = os.path.join(self.python_dir, self.python_installer)
        
        # 确保resources目录存在
        if not os.path.exists(self.python_dir):
            os.makedirs(self.python_dir)

    def get_versions(self) -> List[str]:
        try:
            result = subprocess.run(
                ["git", "ls-remote", "--tags", self.repo_url],
                capture_output=True,
                text=True,
                check=True
            )
            return [line.split('refs/tags/')[-1].strip() 
                   for line in result.stdout.splitlines() 
                   if 'refs/tags/' in line]
        except subprocess.CalledProcessError:
            messagebox.showerror("错误", "无法获取版本列表")
            return []

    def clone_version(self, version: str) -> bool:
        try:
            target_path = os.path.join(self.local_path, version)
            if not os.path.exists(target_path):
                os.makedirs(target_path)
                subprocess.run(
                    ["git", "clone", "-b", version, self.repo_url, target_path],
                    check=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                # 安装依赖
                subprocess.run(
                    ["pip", "install", "-r", f"{target_path}/requirements.txt"],
                    check=True
                )
            return True
        except Exception as e:
            messagebox.showerror("错误", f"部署失败: {str(e)}")
            return False

    def install_python(self) -> bool:
        try:
            if os.path.exists(self.python_path):
                subprocess.run(
                    [self.python_path, "/quiet", "InstallAllUsers=1", "PrependPath=1"],
                    check=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                return True
            else:
                messagebox.showerror("错误", f"Python安装包不存在: {self.python_path}")
                return False
        except Exception as e:
            messagebox.showerror("错误", f"Python安装失败: {str(e)}")
            return False

    def start_bot(self, version: str) -> bool:
        try:
            bot_path = os.path.join(self.local_path, version)
            subprocess.Popen(
                ["python", "bot.py"],
                cwd=bot_path
            )
            return True
        except Exception:
            return False
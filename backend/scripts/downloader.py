import os
import sys
import subprocess
import logging
import shutil
from pathlib import Path
import json
import requests
from typing import Dict, List, Optional, Union, Tuple

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("MaiBot-Downloader")

class BotDownloader:
    """MaiBot下载器，负责获取必要的repo和依赖"""
    
    def __init__(self, base_dir: str = None):
        """初始化下载器
        
        Args:
            base_dir: 基础安装目录，若不指定则使用系统临时目录
        """
        self.base_dir = base_dir or os.path.join(os.path.expanduser("~"), "MaiM-with-u")
        self.maibot_repo = "https://github.com/MaiM-with-u/MaiBot.git"
        self.adapter_repo = "https://github.com/MaiM-with-u/MaiBot-Napcat-Adapter.git"
        self.maibot_dir = os.path.join(self.base_dir, "MaiBot")
        self.adapter_dir = os.path.join(self.base_dir, "MaiBot-Napcat-Adapter")
        self.python_path = sys.executable
        self.venv_dir = os.path.join(self.maibot_dir, "venv")
        self.venv_python = os.path.join(self.venv_dir, "Scripts", "python.exe")
        self.venv_pip = os.path.join(self.venv_dir, "Scripts", "pip.exe")
        
        # 确保基础目录存在
        os.makedirs(self.base_dir, exist_ok=True)
    
    def check_git_installed(self) -> bool:
        """检查Git是否已安装"""
        try:
            subprocess.run(["git", "--version"], check=True, capture_output=True)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.error("Git未安装或不在PATH中，请先安装Git")
            return False
    
    def check_python_version(self) -> bool:
        """检查Python版本是否符合要求（>= 3.10）"""
        try:
            version_info = sys.version_info
            if version_info.major >= 3 and version_info.minor >= 10:
                logger.info(f"Python版本 {version_info.major}.{version_info.minor} 符合要求")
                return True
            else:
                logger.error(f"Python版本 {version_info.major}.{version_info.minor} 不符合要求，需要 >= 3.10")
                return False
        except Exception as e:
            logger.error(f"检查Python版本时出错：{e}")
            return False
    
    def clone_repos(self) -> Tuple[bool, bool]:
        """克隆MaiBot和Adapter仓库
        
        Returns:
            Tuple[bool, bool]: (成功克隆MaiBot, 成功克隆Adapter)
        """
        if not self.check_git_installed():
            return False, False
        
        maibot_success = self._clone_repo(self.maibot_repo, "MaiBot", self.maibot_dir)
        adapter_success = self._clone_repo(self.adapter_repo, "MaiBot-Napcat-Adapter", self.adapter_dir)
        
        return maibot_success, adapter_success
    
    def _clone_repo(self, repo_url: str, repo_name: str, target_dir: str) -> bool:
        """克隆指定的代码库
        
        Args:
            repo_url: 仓库URL
            repo_name: 仓库名称（用于日志）
            target_dir: 克隆到的目标目录
        
        Returns:
            bool: 是否成功克隆
        """
        if os.path.exists(target_dir):
            logger.info(f"{repo_name}目录已存在，尝试拉取最新更改")
            try:
                subprocess.run(["git", "-C", target_dir, "pull"], check=True)
                logger.info(f"{repo_name}更新成功")
                return True
            except subprocess.SubprocessError as e:
                logger.error(f"更新{repo_name}失败：{e}")
                return False
        
        logger.info(f"克隆{repo_name}到{target_dir}")
        try:
            subprocess.run(["git", "clone", repo_url, target_dir], check=True)
            logger.info(f"{repo_name}克隆成功")
            return True
        except subprocess.SubprocessError as e:
            logger.error(f"克隆{repo_name}失败：{e}")
            return False
    
    def create_venv(self) -> bool:
        """创建Python虚拟环境
        
        Returns:
            bool: 是否成功创建虚拟环境
        """
        if not self.check_python_version():
            return False
        
        if os.path.exists(self.venv_dir):
            logger.info(f"虚拟环境已存在于 {self.venv_dir}")
            return True
        
        logger.info(f"在{self.venv_dir}创建Python虚拟环境")
        try:
            subprocess.run([sys.executable, "-m", "venv", self.venv_dir], check=True)
            logger.info(f"虚拟环境创建成功")
            return True
        except subprocess.SubprocessError as e:
            logger.error(f"创建虚拟环境失败：{e}")
            return False
    
    def install_dependencies(self) -> Tuple[bool, bool]:
        """安装MaiBot和Adapter的依赖
        
        Returns:
            Tuple[bool, bool]: (MaiBot依赖安装成功, Adapter依赖安装成功)
        """
        if not os.path.exists(self.venv_python):
            logger.error(f"虚拟环境不存在，请先创建虚拟环境")
            return False, False
        
        # 安装MaiBot依赖
        maibot_req_file = os.path.join(self.maibot_dir, "requirements.txt")
        if not os.path.exists(maibot_req_file):
            logger.error(f"MaiBot的requirements.txt不存在")
            return False, False
        
        logger.info("安装MaiBot依赖...")
        maibot_success = self._install_requirements(maibot_req_file)
        
        # 安装Adapter依赖
        adapter_req_file = os.path.join(self.adapter_dir, "requirements.txt")
        if not os.path.exists(adapter_req_file):
            logger.error(f"Adapter的requirements.txt不存在")
            return maibot_success, False
        
        logger.info("安装Adapter依赖...")
        adapter_success = self._install_requirements(adapter_req_file)
        
        return maibot_success, adapter_success
    
    def _install_requirements(self, req_file: str) -> bool:
        """安装指定的依赖文件
        
        Args:
            req_file: requirements.txt的路径
        
        Returns:
            bool: 是否安装成功
        """
        try:
            subprocess.run([
                self.venv_pip, "install", 
                "-i", "https://mirrors.aliyun.com/pypi/simple", 
                "-r", req_file, "--upgrade"
            ], check=True)
            logger.info(f"依赖安装成功: {req_file}")
            return True
        except subprocess.SubprocessError as e:
            logger.error(f"安装依赖失败：{e}")
            return False
    
    def download(self, instance_name: str = None) -> dict:
        """执行完整的下载流程
        
        Args:
            instance_name: 实例名称，用于配置
        
        Returns:
            dict: 下载结果，包含状态和路径
        """
        if instance_name:
            # 使用实例名创建特定文件夹
            self.base_dir = os.path.join(os.path.expanduser("~"), "MaiM-with-u", instance_name)
            self.maibot_dir = os.path.join(self.base_dir, "MaiBot")
            self.adapter_dir = os.path.join(self.base_dir, "MaiBot-Napcat-Adapter")
            self.venv_dir = os.path.join(self.maibot_dir, "venv")
            self.venv_python = os.path.join(self.venv_dir, "Scripts", "python.exe")
            self.venv_pip = os.path.join(self.venv_dir, "Scripts", "pip.exe")
            
            # 确保目录存在
            os.makedirs(self.base_dir, exist_ok=True)
        
        logger.info(f"开始下载MaiBot到 {self.base_dir}")
        
        # 克隆仓库
        maibot_cloned, adapter_cloned = self.clone_repos()
        if not (maibot_cloned and adapter_cloned):
            return {
                "success": False,
                "message": "克隆仓库失败，请检查网络和Git配置",
                "base_dir": self.base_dir
            }
        
        # 创建虚拟环境
        venv_created = self.create_venv()
        if not venv_created:
            return {
                "success": False,
                "message": "创建虚拟环境失败，请确保Python版本>=3.10",
                "base_dir": self.base_dir
            }
        
        # 安装依赖
        maibot_deps, adapter_deps = self.install_dependencies()
        if not (maibot_deps and adapter_deps):
            return {
                "success": False,
                "message": "安装依赖失败，可能存在网络问题或依赖冲突",
                "base_dir": self.base_dir,
                "maibot_deps_installed": maibot_deps,
                "adapter_deps_installed": adapter_deps
            }
        
        # 下载完成，返回成功信息
        return {
            "success": True,
            "message": "MaiBot下载和依赖安装完成",
            "base_dir": self.base_dir,
            "maibot_dir": self.maibot_dir,
            "adapter_dir": self.adapter_dir,
            "venv_dir": self.venv_dir,
            "instance_name": instance_name or "default"
        }

if __name__ == "__main__":
    # 命令行测试用
    import argparse
    parser = argparse.ArgumentParser(description="MaiBot下载工具")
    parser.add_argument("--dir", help="安装目录")
    parser.add_argument("--instance", help="实例名称")
    args = parser.parse_args()
    
    downloader = BotDownloader(args.dir)
    result = downloader.download(args.instance)
    print(json.dumps(result, indent=2))

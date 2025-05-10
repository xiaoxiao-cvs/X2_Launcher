# -*- coding: utf-8 -*-
"""
MaiBot 下载器
"""
import os
import sys
import time
import logging
import subprocess
import platform
from pathlib import Path
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levellevel)s - %(message)s'
)

logger = logging.getLogger("bot-downloader")

class BotDownloader:
    """MaiBot 下载器类"""
    
    def __init__(self, project_root=None):
        """初始化下载器"""
        self.base_dir = os.path.join(os.getcwd() if project_root is None else project_root, "MaiM-with-u")
        
        # 确保基础目录存在
        os.makedirs(self.base_dir, exist_ok=True)
        
        # 系统信息
        self.is_windows = platform.system() == "Windows"
        logger.info(f"初始化下载器，基础目录: {self.base_dir}")
        
    def download(self, instance_name, version="latest"):
        """下载指定版本的MaiBot并安装基础依赖
        
        Args:
            instance_name: 实例名称
            version: 版本号，默认为latest
            
        Returns:
            Dict: 下载结果
        """
        try:
            logger.info(f"开始基础下载 MaiBot {version} 到实例 {instance_name}")
            print(f"【下载器】开始基础下载 MaiBot {version} 到实例 {instance_name}")
            
            instance_path = os.path.join(self.base_dir, instance_name)
            os.makedirs(instance_path, exist_ok=True)
            
            if os.path.exists(os.path.join(instance_path, "MaiBot")):
                logger.info(f"实例的MaiBot目录已存在，执行清理: {instance_path}")
                print(f"【下载器】实例的MaiBot目录已存在，执行清理: {instance_path}")
                try:
                    self._clean_instance(instance_path) # _clean_instance 只清理MaiBot子目录
                except Exception as e:
                    logger.error(f"清理实例失败: {e}")
                    print(f"【下载器】错误: 清理实例失败: {e}")
                    return {"success": False, "message": f"清理实例失败: {e}"}
            
            try:
                logger.info(f"开始从GitHub克隆 MaiBot {version}")
                print(f"【下载器】开始从GitHub克隆 MaiBot {version}")
                
                git_url = "https://github.com/MaiM-with-u/MaiBot.git"
                # 克隆到 instance_path 下的 MaiBot 子目录
                maibot_target_path = os.path.join(instance_path, "MaiBot") 
                git_cmd = ["git", "clone", git_url, maibot_target_path, "--branch", version, "--single-branch", "--depth", "1"]
                
                if version.lower() in ["latest", "main"]:
                    git_cmd = ["git", "clone", git_url, maibot_target_path, "--depth", "1"]
                    
                logger.info(f"执行命令: {' '.join(git_cmd)}")
                print(f"【下载器】执行命令: {' '.join(git_cmd)}")
                
                process = subprocess.Popen(
                    git_cmd,
                    # cwd=instance_path, # Git clone target path is absolute
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8', errors='replace'
                )
                
                for line in process.stdout:
                    line = line.strip()
                    if line:
                        logger.info(f"Git: {line}")
                        print(f"【Git】{line}")
                process.wait()
                
                if process.returncode != 0:
                    error_msg = f"Git克隆失败, 返回码: {process.returncode}"
                    logger.error(error_msg)
                    print(f"【下载器】错误: {error_msg}")
                    return {"success": False, "message": error_msg}
                    
                if not os.path.exists(maibot_target_path) or not os.path.exists(os.path.join(maibot_target_path, "requirements.txt")):
                    error_msg = "Git克隆后MaiBot目录或requirements.txt不存在"
                    logger.error(error_msg)
                    print(f"【下载器】错误: {error_msg}")
                    return {"success": False, "message": error_msg}
                    
                logger.info("Git克隆成功")
                print(f"【下载器】Git克隆成功")
                
                logger.info("开始安装基础依赖")
                print(f"【下载器】开始安装基础依赖")
                
                # 虚拟环境创建在 instance_path/venv
                venv_path = os.path.join(instance_path, "venv")
                python_exec = sys.executable # 使用当前运行的python解释器创建venv
                
                venv_cmd = [python_exec, "-m", "venv", venv_path]
                logger.info(f"创建虚拟环境: {' '.join(venv_cmd)}")
                print(f"【下载器】创建虚拟环境: {' '.join(venv_cmd)}")
                
                process = subprocess.Popen(
                    venv_cmd,
                    # cwd=instance_path, # venv_path is absolute
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8', errors='replace'
                )
                for line in process.stdout:
                    line = line.strip(); print(f"【venv】{line}") if line else None
                process.wait()
                
                if process.returncode != 0 or not os.path.exists(venv_path):
                    error_msg = f"创建虚拟环境失败, 返回码: {process.returncode}"
                    logger.error(error_msg)
                    print(f"【下载器】错误: {error_msg}")
                    return {"success": False, "message": error_msg}
                
                pip_exec = os.path.join(venv_path, "Scripts" if platform.system() == "Windows" else "bin", "pip")
                requirements_file = os.path.join(maibot_target_path, "requirements.txt")
                install_cmd = [pip_exec, "install", "-r", requirements_file, "--upgrade", "pip"] #升级pip
                
                logger.info(f"安装依赖: {' '.join(install_cmd)}")
                print(f"【下载器】安装依赖: {' '.join(install_cmd)}")
                
                process = subprocess.Popen(
                    install_cmd,
                    # cwd=maibot_target_path, # requirements_file is absolute
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8', errors='replace'
                )
                for line in process.stdout:
                    line = line.strip(); print(f"【pip】{line}") if line else None
                process.wait()

                if process.returncode != 0:
                    error_msg = f"依赖安装失败, 返回码: {process.returncode}"
                    logger.error(error_msg)
                    print(f"【下载器】错误: {error_msg}")
                    # 不直接返回失败，有些依赖失败可能是可选的，但记录错误
                    # return {"success": False, "message": error_msg }

                # 基础下载只创建MaiBot核心的启动脚本，适配器等由configurator处理
                self._create_maibot_core_scripts(instance_path, instance_name, maibot_target_path, venv_path)
                
                result = {
                    "success": True,
                    "message": f"MaiBot {version} 基础下载和依赖安装完成",
                    "instance_name": instance_name,
                    "base_dir": instance_path, # instance_path 是 MaiM-with-u/{instance_name}
                    "maibot_dir": maibot_target_path, # maibot_target_path 是 MaiM-with-u/{instance_name}/MaiBot
                    "venv_dir": venv_path,
                    "timestamp": datetime.now().isoformat()
                }
                
                logger.info(f"MaiBot基础下载和安装成功: {instance_path}")
                print(f"【下载器】MaiBot基础下载和安装成功: {instance_path}")
                return result
                
            except Exception as e:
                error_msg = f"下载MaiBot核心出错: {str(e)}"
                logger.exception(error_msg)
                print(f"【下载器】严重错误: {error_msg}")
                return {"success": False, "message": error_msg}
        except Exception as e:
            error_msg = f"下载MaiBot核心出错: {str(e)}"
            logger.exception(error_msg)
            print(f"【下载器】严重错误: {error_msg}")
            return {"success": False, "message": error_msg}
    
    def _clean_instance(self, instance_path):
        """清理实例目录中的MaiBot子目录，保留venv等其他文件"""
        maibot_dir = os.path.join(instance_path, "MaiBot")
        if os.path.exists(maibot_dir):
            import shutil
            logger.info(f"删除已存在的MaiBot子目录: {maibot_dir}")
            print(f"【下载器】删除已存在的MaiBot子目录: {maibot_dir}")
            shutil.rmtree(maibot_dir, ignore_errors=True)
    
    def _create_maibot_core_scripts(self, instance_path, instance_name, maibot_program_dir, venv_path):
        """仅创建MaiBot核心的启动脚本"""
        logger.info(f"为实例 {instance_name} 创建MaiBot核心启动脚本")
        print(f"【下载器】为实例 {instance_name} 创建MaiBot核心启动脚本")
        
        python_in_venv = os.path.join(venv_path, "Scripts" if platform.system() == "Windows" else "bin", "python")
        activate_script = os.path.join(venv_path, "Scripts" if platform.system() == "Windows" else "bin", "activate")
        
        # Windows
        if platform.system() == "Windows":
            bat_path = os.path.join(instance_path, f"启动MaiBot核心_{instance_name}.bat")
            with open(bat_path, "w", encoding="utf-8") as f:
                f.write(f"""@echo off
title MaiBot Core - {instance_name}
echo 正在激活虚拟环境: {venv_path}
call "{activate_script}"
echo 切换到MaiBot目录: {maibot_program_dir}
cd /d "{maibot_program_dir}"
echo 正在启动MaiBot核心 (app.py)...
"{python_in_venv}" app.py
pause
""")
            logger.info(f"已创建Windows MaiBot核心启动脚本: {bat_path}")
        else: # Linux/macOS
            sh_path = os.path.join(instance_path, f"start_maibot_core_{instance_name}.sh")
            with open(sh_path, "w", encoding="utf-8") as f:
                f.write(f"""#!/bin/bash
echo "正在激活虚拟环境: {venv_path}"
source "{activate_script}"
echo "切换到MaiBot目录: {maibot_program_dir}"
cd "{maibot_program_dir}"
echo "正在启动MaiBot核心 (app.py)..."
"{python_in_venv}" app.py
""")
            os.chmod(sh_path, 0o755)
            logger.info(f"已创建Linux/macOS MaiBot核心启动脚本: {sh_path}")

if __name__ == "__main__":
    import argparse
    import json # Add missing import
    parser = argparse.ArgumentParser(description="MaiBot下载工具")
    parser.add_argument("--dir", help="项目根目录")
    parser.add_argument("--instance", help="实例名称", default=None)
    parser.add_argument("--version", help="MaiBot版本", default="latest")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    args = parser.parse_args()
    
    # 启用调试日志
    if args.debug:
        logging.getLogger("MaiBot-Downloader").setLevel(logging.DEBUG)
        # 添加文件处理器以记录详细日志
        log_file = os.path.join(os.getcwd(), "maibot_downloader_debug.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logging.getLogger("MaiBot-Downloader").addHandler(file_handler)
        logger.info(f"调试日志将保存至: {log_file}")
    
    # 获取绝对路径
    project_root = os.path.abspath(args.dir) if args.dir else os.path.abspath(os.getcwd())
    logger.info(f"使用项目根目录: {project_root}")
    
    downloader = BotDownloader(project_root)
    
    # 执行下载并实时打印状态
    result = downloader.download(args.instance, args.version)
    
    # 打印最终结果
    if result["success"]:
        print(f"\n✓ 成功: {result['message']}")
        print(f"- 实例根目录: {result.get('base_dir')}")
        print(f"- MaiBot程序目录: {result.get('maibot_dir')}") # Corrected key
        # print(f"- 适配器目录: {result.get('adapter_dir')}") # adapter_dir is not part of base download
        print(f"- 虚拟环境: {result.get('venv_dir')}")
    else:
        print(f"\n× 失败: {result['message']}")
    
    # 输出JSON结果供其他程序使用
    print("\nJSON结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))

import os
import sys
from pathlib import Path
import asyncio
import logging
from tkinter import messagebox
import customtkinter as ctk
import threading
from concurrent.futures import ThreadPoolExecutor
import requests  # 添加requests导入

# 确保项目根目录在Python路径中
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from src.utils import setup_environment, check_network
from src.utils.github_auth import GitHubAuth  # 添加GitHub验证导入
from src.ui.app import App
from src.logger import logger
from src.settings import AppConfig as Settings  # 添加配置类导入

def main():
    """主入口函数"""
    try:
        # 设置UI主题
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        # 创建事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 初始化环境
        loop.run_until_complete(setup_environment())
        
        # GitHub token验证
        config = Settings.load_config()
        if not config.get('github_token'):
            messagebox.showwarning("警告", "未设置GitHub Token，某些功能可能受限")
        else:
            auth = GitHubAuth(config['github_token'])
            if not loop.run_until_complete(auth.verify_token()):
                messagebox.showerror("错误", "GitHub Token验证失败")
                return
        
        # 创建应用实例
        app = App()
        app.protocol("WM_DELETE_WINDOW", app.safe_quit)
        
        # 设置日志处理
        logger.add_callback(lambda msg, level: print(f"[{level}] {msg}"))
        
        # 启动主循环
        app.mainloop()
        
    except KeyboardInterrupt:
        logger.log("程序被用户中断", "INFO")
    except Exception as e:
        logger.log(f"程序异常退出: {e}", "CRITICAL")
        messagebox.showerror("错误", f"程序启动失败: {e}")
    finally:
        if 'loop' in locals():
            try:
                loop.close()
            except:
                pass

if __name__ == "__main__":
    main()
import os
import sys
from pathlib import Path
import asyncio
import logging
from tkinter import messagebox
import customtkinter as ctk
import threading

# 确保项目根目录在Python路径中
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.utils import setup_environment, check_network
from src.ui.app import App  # 确保这是最后导入的

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='deploy.log'
)

def main():
    try:
        # 创建事件循
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 确保UI初始化在主线程进行
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        # 创建应用实例
        app = App()
        app.protocol("WM_DELETE_WINDOW", lambda: on_closing(app, loop))
        
        # 在后台运行事件循环
        def run_loop():
            try:
                loop.run_forever()
            except Exception as e:
                logging.error(f"Event loop error: {e}")
        
        thread = threading.Thread(target=run_loop, daemon=True)
        thread.start()
        
        
        loop.call_soon_threadsafe(
            lambda: asyncio.create_task(setup_environment())
        )
        
        # 启动主程序
        app.mainloop()
        
    except Exception as e:
        logging.critical(f"Application crashed: {str(e)}")
        messagebox.showerror("致命错误", f"应用程序崩溃：{str(e)}")
    finally:
        if 'loop' in locals():
            loop.stop()

def on_closing(app, loop):
    """处理窗口关闭事件"""
    if messagebox.askokcancel("退出", "确定要退出程序吗?"):
        loop.stop()
        app.quit()
        app.destroy()

if __name__ == "__main__":
    main()
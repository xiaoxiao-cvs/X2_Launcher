import customtkinter as ctk
from tkinter import ttk, messagebox
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
import asyncio
import threading
import uvicorn

from ..config import Config
from ..settings import Settings
from ..version_manager import VersionController
from ..backend import app as backend_app
from .components import SettingsWindow

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # 初始化样式
        self.style = ttk.Style()
        
        # 初始化基本服务
        self.settings = Settings()
        self.config = Config()
        self.controller = VersionController(self.config)
        self.thread_pool = ThreadPoolExecutor(max_workers=3)
        self.is_busy = False
        self.loop = asyncio.get_event_loop()
        
        # 设置基本窗口属性
        self.title("𝕏² Deploy Station")
        self.setup_window()
        
        # 初始化UI组件
        self.setup_ui()
        self.init_services()

    def init_services(self):
        """初始化后端服务"""
        self.controller.set_log_callback(self._log_message_handler)
        backend_app.init_controller(self.config)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.after(100, self.refresh_versions)
        self.start_backend()

    def setup_window(self):
        """设置窗口基本属性"""
        size = self.settings.get("appearance", "window_size")
        self.geometry(size)
        self.minsize(800, 450)
        
        # 设置背景
        self.bg_image = None
        bg_path = self.settings.get("appearance", "background_image")
        if os.path.exists(bg_path):
            try:
                image = Image.open(bg_path)
                self.bg_image = ctk.CTkImage(
                    light_image=image,
                    dark_image=image,
                    size=(1280, 720)
                )
                self.bg_label = ctk.CTkLabel(
                    self,
                    image=self.bg_image,
                    text=""
                )
                self.bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)
            except Exception as e:
                logging.error(f"背景图片加载失败: {e}")

    def setup_ui(self):
        """设置UI组件"""
        # 避免阻塞的UI初始化
        self.after(0, self._create_ui_components)

    def _create_ui_components(self):
        """实际创建UI组件的方法"""
        try:
            # 创建主框架
            self.main_frame = ctk.CTkFrame(
                self,
                fg_color=("gray90", "gray10")
            )
            self.main_frame.place(relx=0.5, rely=0.5, relwidth=0.8, relheight=0.8, anchor="center")
            
            # 设置样式和创建组件
            self.setup_styles()
            self.create_settings_button()
            self.create_title_section()
            self.create_version_section()
            self.create_log_section()
            self.create_button_section()
            self.create_loading_label()
            
        except Exception as e:
            logging.error(f"UI创建失败: {e}")
            messagebox.showerror("错误", f"UI初始化失败: {e}")

    def setup_styles(self):
        """设置界面样式"""
        transparency = self.settings.get("appearance", "transparency")
        accent_color = self.settings.get("appearance", "accent_color")
        try:
            rgb = self._adjust_color(accent_color, transparency)
            self.style.configure(
                "Modern.Horizontal.TProgressbar",
                troughcolor="#2b2b2b",
                background=f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}",
                thickness=10
            )
        except Exception as e:
            logging.error(f"设置样式失败: {e}")
            self.style.configure(
                "Modern.Horizontal.TProgressbar",
                troughcolor="#2b2b2b",
                background="#1E90FF",
                thickness=10
            )

    def _log_message_handler(self, message, level="INFO"):
        """内部日志处理方法"""
        if hasattr(self, 'log_text'):  # 确保UI已初始化
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] [{level}] {message}\n"
            self.log_text.insert("end", log_entry)
            self.log_text.see("end")
        logging.info(message)

    def start_backend(self):
        def run_server():
            try:
                config = uvicorn.Config(
                    backend_app.app,
                    host="127.0.0.1",
                    port=8000,
                    log_level="error"
                )
                server = uvicorn.Server(config)
                self.loop.run_until_complete(server.serve())
            except Exception as e:
                self.log_message(f"后端服务器启动失败: {e}", "ERROR")
        
        threading.Thread(target=run_server, daemon=True).start()

    def create_settings_button(self):
        """创建设置按钮"""
        self.settings_button = ctk.CTkButton(
            self.main_frame,
            text="设置",
            width=30,
            command=self.open_settings
        )
        self.settings_button.place(relx=0.95, rely=0.05, anchor="ne")

    def create_title_section(self):
        """创建标题区域"""
        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="𝕏² Deploy Station",
            font=("Arial", 24, "bold")
        )
        self.title_label.place(relx=0.5, rely=0.1, anchor="center")

    def create_version_section(self):
        """创建版本选择区域"""
        self.version_frame = ctk.CTkFrame(self.main_frame)
        self.version_frame.place(relx=0.5, rely=0.25, anchor="center", relwidth=0.9)
        
        self.version_label = ctk.CTkLabel(
            self.version_frame,
            text="选择版本："
        )
        self.version_label.pack(side="left", padx=10)
        
        self.version_combobox = ctk.CTkComboBox(
            self.version_frame,
            values=["加载中..."],
            width=200
        )
        self.version_combobox.pack(side="left", padx=10)

    def create_log_section(self):
        """创建日志区域"""
        self.log_frame = ctk.CTkFrame(self.main_frame)
        self.log_frame.place(relx=0.5, rely=0.6, anchor="center", relwidth=0.9, relheight=0.5)
        
        self.log_text = ctk.CTkTextbox(
            self.log_frame,
            wrap="word"
        )
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)

    def create_button_section(self):
        """创建按钮区域"""
        self.button_frame = ctk.CTkFrame(self.main_frame)
        self.button_frame.place(relx=0.5, rely=0.9, anchor="center")
        
        self.deploy_button = ctk.CTkButton(
            self.button_frame,
            text="部署",
            command=self.deploy_selected_version
        )
        self.deploy_button.pack(side="left", padx=10)
        
        self.start_button = ctk.CTkButton(
            self.button_frame,
            text="启动",
            command=self.start_selected_version
        )
        self.start_button.pack(side="left", padx=10)

    def create_loading_label(self):
        """创建加载提示标签"""
        self.loading_label = ctk.CTkLabel(
            self.main_frame,
            text="",
            text_color="gray"
        )
        self.loading_label.place(relx=0.5, rely=0.4, anchor="center")

    def open_settings(self):
        """打开设置窗口"""
        settings_window = SettingsWindow(self)
        settings_window.focus()

    def refresh_versions(self):
        """刷新版本列表"""
        try:
            versions = self.controller.get_versions()
            self.version_combobox.configure(values=versions)
            if versions and versions[0] != "NaN":
                self.version_combobox.set(versions[0])
        except Exception as e:
            self.log_message(f"刷新版本列表失败: {e}", "ERROR")

    def deploy_selected_version(self):
        """部署选中的版本"""
        if self.is_busy:
            return
        version = self.version_combobox.get()
        self.is_busy = True
        self.loading_label.configure(text="正在部署...")
        
        def deploy():
            try:
                success = self.controller.clone_version(version)
                self.after(0, lambda: self.deployment_complete(success))
            except Exception as e:
                self.after(0, lambda: self.deployment_complete(False, str(e)))
        
        self.thread_pool.submit(deploy)

    def deployment_complete(self, success, error=None):
        """部署完成的回调"""
        self.is_busy = False
        self.loading_label.configure(text="")
        if success:
            messagebox.showinfo("成功", "部署完成")
        else:
            messagebox.showerror("错误", f"部署失败: {error if error else '未知错误'}")

    def start_selected_version(self):
        """启动选中的版本"""
        if self.is_busy:
            return
        version = self.version_combobox.get()
        success = self.controller.start_bot(version)
        if success:
            self.log_message("机器人启动成功")
        else:
            self.log_message("机器人启动失败", "ERROR")

    def on_closing(self):
        """处理窗口关闭事件"""
        if messagebox.askokcancel("退出", "确定要退出程序吗?"):
            self.controller.stop_bot()
            self.thread_pool.shutdown(wait=False)
            self.quit()
            self.destroy()

    def log_message(self, message, level="INFO"):
        """添加日志消息"""
        if hasattr(self, 'log_text'):
            self.log_text.insert("end", f"[{level}] {message}\n")
            self.log_text.see("end")

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
import queue
from typing import Tuple, Optional

from ..config import Config
from ..settings import AppConfig as Settings  # 更新为新的配置类
from ..version_manager import VersionController
from ..backend import app as backend_app
from .components import SettingsWindow
from ..logger import XLogger  # 更新logger导入

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self._init_services()
        self.title("𝕏² Deploy Station")
        self.setup_window()
        self.setup_ui()
        
        # 初始化完成后立即刷新版本列表
        self.after(100, self._init_versions)
        
        # 添加消息队列
        self.log_queue = queue.Queue()
        self.status_queue = queue.Queue()
        
        # 启动队列处理
        self.after(100, self.process_queues)
        
        # 使用XLogger替代logger
        XLogger.log("启动X² Launcher")
        
    def _init_services(self):
        """初始化基础服务"""
        self.style = ttk.Style()
        self.settings = Settings()
        self.config = Config()
        self.controller = VersionController(self.config)
        self.thread_pool = ThreadPoolExecutor(max_workers=3)
        self.is_busy = False
        
        # 设置回调和后端
        self.controller.set_log_callback(self.log_callback)
        backend_app.init_controller(self.config)
        self.start_backend()
        # 注册日志回调
        XLogger.add_callback(self.log_callback)

    def _init_versions(self):
        """初始化版本列表"""
        def fetch_versions():
            try:
                versions = self.controller.get_versions()
                if versions and versions[0] != "NaN":
                    self.after(0, lambda: self.version_combobox.configure(values=versions))
                    self.after(0, lambda: self.version_combobox.set(versions[0]))
                else:
                    self.after(0, lambda: self.version_combobox.configure(values=["暂无可用版本"]))
            except Exception as e:
                XLogger.log(f"版本列表获取失败: {e}", "ERROR")
                self.after(0, lambda: self.version_combobox.configure(values=["加载失败"]))
        
        self.thread_pool.submit(fetch_versions)

    def setup_window(self):
        """设置窗口属性和背景"""
        try:
            size = self.settings.get("appearance", "window_size")
            self.geometry(size)
            self.minsize(800, 450)
            self._setup_background()
        except Exception as e:
            logging.error(f"窗口设置失败: {e}")
            
    def _setup_background(self):
        """设置背景图片"""
        bg_path = self.settings.get("appearance", "background_image")
        if not os.path.exists(bg_path):
            return
            
        try:
            image = Image.open(bg_path)
            self.bg_image = ctk.CTkImage(
                light_image=image,
                dark_image=image,
                size=(1280, 720)
            )
            ctk.CTkLabel(
                self,
                image=self.bg_image,
                text=""
            ).place(relx=0, rely=0, relwidth=1, relheight=1)
        except Exception as e:
            logging.error(f"背景图片加载失败: {e}")

    def setup_ui(self):
        """设置UI组件"""
        # 避免阻塞的UI初始化
        self.after(1, self._create_ui_components)
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
        try:
            transparency = float(self.settings.get("appearance", "transparency"))
            accent_color = self.settings.get("appearance", "accent_color")
            rgb = self._adjust_color(accent_color, transparency)
            
            self.style.configure(
                "Modern.Horizontal.TProgressbar",
                troughcolor="#2b2b2b",
                background=f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}",
                thickness=10
            )
        except Exception as e:
            logging.error(f"设置样式失败: {e}")
            # 使用默认样式
            self.style.configure(
                "Modern.Horizontal.TProgressbar",
                troughcolor="#2b2b2b",
                background="#1E90FF",
                thickness=10
            )

    def _adjust_color(self, color_hex: str, transparency: float) -> tuple:
        """调整颜色透明度"""
        try:
            # 移除井号并转换为RGB
            color = color_hex.lstrip('#')
            rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
            
            # 根据透明度调整
            adjusted = tuple(int(c * float(transparency)) for c in rgb)
            return adjusted
        except Exception as e:
            logging.error(f"颜色调整失败: {e}")
            return (30, 144, 255)  # 返回默认蓝色

    def _log_message_handler(self, message, level="INFO"):
        """处理日志消息"""
        if hasattr(self, 'log_text'):
            try:
                self.log_text.insert("end", f"{message}\n")
                self.log_text.see("end")
            except Exception as e:
                print(f"UI日志更新失败: {e}")

    def start_backend(self):
        """启动后端服务"""
        async def start_server():
            config = uvicorn.Config(
                backend_app.app,
                host="127.0.0.1",
                port=8000,
                log_level="error",
                reload=True  # 开发环境支持热重载
            )
            server = uvicorn.Server(config)
            await server.serve()
            
        def run():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(start_server())
            except Exception as e:
                self.log_message(f"后端服务器启动失败: {e}", "ERROR")
                
        threading.Thread(target=run, daemon=True).start()

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
            values=["正在加载..."],
            width=200,
            state="readonly"  # 添加只读状态
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
    # 将设置窗口保存为实例变量，防止被垃圾回收
        self.settings_window = SettingsWindow(self)
        self.settings_window.focus()
    def refresh_versions(self):
        """刷新版本列表"""
        try:
            versions = self.controller.get_versions()
            if not versions:
                versions = ["暂无可用版本"]
            self.version_combobox.configure(values=versions)
            self.version_combobox.set(versions[0])
        except Exception as e:
            self.log_message(f"刷新版本列表失败: {e}", "ERROR")
            self.version_combobox.configure(values=["加载失败"])

    def deploy_selected_version(self):
        """改进的部署方法"""
        if self.is_busy:
            return
            
        version = self.version_combobox.get()
        self.is_busy = True
        self.set_status("正在部署...")
        
        # 禁用按钮
        self.deploy_button.configure(state="disabled")
        self.start_button.configure(state="disabled")
        
        def deploy():
            try:
                success = self.controller.clone_version(version)
                if success:
                    self.set_status("", None)
                    messagebox.showinfo("成功", "部署完成")
                else:
                    self.set_status("", "部署失败")
            except Exception as e:
                self.set_status("", f"部署异常: {str(e)}")
            finally:
                self.is_busy = False
                # 恢复按钮状态
                self.after(0, lambda: self.deploy_button.configure(state="normal"))
                self.after(0, lambda: self.start_button.configure(state="normal"))
        
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
        self.start_button.configure(state="disabled")
        
        try:
            success = self.controller.start_bot(version)
            if success:
                self.log_message("机器人启动成功")
            else:
                self.log_message("机器人启动失败", "ERROR")
        finally:
            self.start_button.configure(state="normal")

    def log_message(self, message, level="INFO"):
        """添加日志消息"""
        if hasattr(self, 'log_text'):
            self.log_text.insert("end", f"[{level}] {message}\n")
            self.log_text.see("end")

    def safe_quit(self):
        """安全退出应用"""
        try:
            # 停止所有活动进程
            if hasattr(self, 'controller'):
                self.controller.stop_bot()
                
            # 停止后端服务
            if hasattr(self, 'backend_server'):
                self.backend_server.should_exit = True
                
            # 清理线程池
            if hasattr(self, 'thread_pool'):
                self.thread_pool.shutdown(wait=False)
                
            # 保存配置
            if hasattr(self, 'settings'):
                self.settings.save()
                
            # 退出应用
            self.quit()
            self.destroy()
            
        except Exception as e:
            XLogger.log(f"退出时发生错误: {e}", "ERROR")
            self.quit()
            self.destroy()

    def process_queues(self):
        """处理所有队列消息"""
        try:
            # 处理日志队列
            self._process_log_queue()
            # 处理状态队列
            self._process_status_queue()
            
            # 继续监听队列
            self.after(100, self.process_queues)
        except Exception as e:
            XLogger.log(f"队列处理失败: {e}", "ERROR")
            self.after(100, self.process_queues)

    def _process_log_queue(self):
        """处理日志队列"""
        while not self.log_queue.empty():
            try:
                message, level = self.log_queue.get_nowait()
                self.update_log_ui(message, level)
            except queue.Empty:
                break

    def _process_status_queue(self):
        """处理状态队列"""
        while not self.status_queue.empty():
            try:
                status = self.status_queue.get_nowait()
                self.update_status_ui(status)
            except queue.Empty:
                break

    def update_log_ui(self, message: str, level: str):
        """更新日志UI"""
        try:
            if hasattr(self, 'log_text'):
                self.log_text.insert("end", f"[{level}] {message}\n")
                self.log_text.see("end")
        except Exception as e:
            print(f"UI日志更新失败: {e}")

    def update_status_ui(self, status: Tuple[str, Optional[str]]):
        """更新状态UI"""
        try:
            message, error = status
            if hasattr(self, 'loading_label'):
                self.loading_label.configure(text=message)
            if error and hasattr(self, 'is_busy'):
                self.is_busy = False
                messagebox.showerror("错误", error)
        except Exception as e:
            print(f"UI状态更新失败: {e}")

    def log_callback(self, message: str, level: str = "INFO"):
        """线程安全的日志回调"""
        self.log_queue.put((message, level))

    def set_status(self, message: str, error: Optional[str] = None):
        """线程安全的状态更新"""
        self.status_queue.put((message, error))
    def _set_ui_transparency(self, alpha):
        """设置UI元素透明度（不影响背景）"""
        try:
            # 确保alpha在有效范围内
            alpha = max(0.5, min(1.0, float(alpha)))
        
        # 需要应用透明度的UI组件
            ui_elements = [
                self.main_frame,
                self.version_frame,
                self.log_frame,
                self.button_frame,
                self.title_label,
                self.settings_button,
                self.version_label,
                self.version_combobox,
                self.log_text,
                self.deploy_button,
                self.start_button,
                self.loading_label
            ]
        
            for widget in ui_elements:
                if widget is None:
                    continue
                
                # 对CTk组件应用透明度
                if isinstance(widget, (ctk.CTkFrame, ctk.CTkLabel, ctk.CTkButton, 
                                    ctk.CTkComboBox, ctk.CTkTextbox)):
                    # 获取当前颜色
                    fg_color = widget.cget("fg_color")
                    bg_color = widget.cget("bg_color") if hasattr(widget, "bg_color") else None
                
                    # 应用透明度到前景色
                    if isinstance(fg_color, str):
                        widget.configure(fg_color=self._apply_alpha_to_color(fg_color, alpha))
                    elif isinstance(fg_color, (list, tuple)):
                        widget.configure(fg_color=[self._apply_alpha_to_color(c, alpha) for c in fg_color])
                
                    # 应用透明度到背景色
                    if bg_color:
                        if isinstance(bg_color, str):
                            widget.configure(bg_color=self._apply_alpha_to_color(bg_color, alpha))
                        elif isinstance(bg_color, (list, tuple)):
                            widget.configure(bg_color=[self._apply_alpha_to_color(c, alpha) for c in bg_color])
        
            # 保存透明度设置
            self.settings.set("appearance", "transparency", str(alpha))
            self.settings.save()
        
        except Exception as e:
            XLogger.error(f"设置透明度失败: {e}")

    def _apply_alpha_to_color(self, color, alpha):
        """给颜色添加透明度"""
        if isinstance(color, str) and color.startswith("#"):
            # 处理十六进制颜色
            hex_color = color.lstrip('#')
            rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}{int(255*alpha):02x}"
        elif isinstance(color, (list, tuple)):
            # 处理RGBA颜色
            return (*color[:3], int(255*alpha))
        return color
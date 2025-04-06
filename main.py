import customtkinter as ctk
from functools import partial
import threading
import asyncio
from src.version_manager import VersionController
from tkinter import ttk
import time
from src.backend.app import app

class ModernProgressBar(ttk.Progressbar):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.configure(style="Modern.Horizontal.TProgressbar")
        
    def start_progress(self, duration=1.0):
        self.configure(value=0)
        self.step_size = 100 / (duration * 10)
        self._update_progress()
        
    def _update_progress(self):
        current = self['value']
        if current < 100:
            self.step(self.step_size)
            self.after(100, self._update_progress)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("𝕏² Deploy Station")
        self.geometry("600x400")
        self._setup_styles()
        self._init_ui()
        
    def _setup_styles(self):
        self.style = ttk.Style()
        self.style.configure(
            "Modern.Horizontal.TProgressbar",
            troughcolor='#2b2b2b',
            background='#00ff00',
            thickness=10
        )
        
    def _init_ui(self):
        # 主容器
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 标题
        title = ctk.CTkLabel(
            self.main_frame, 
            text="MaiBot 部署站",
            font=("Segoe UI", 24, "bold")
        )
        title.pack(pady=20)
        
        # 版本选择区域
        self.version_frame = ctk.CTkFrame(self.main_frame)
        self.version_frame.pack(fill="x", padx=30, pady=10)
        
        self.version_label = ctk.CTkLabel(
            self.version_frame,
            text="选择版本：",
            font=("Segoe UI", 14)
        )
        self.version_label.pack(side="left", padx=10)
        
        self.version_var = ctk.StringVar(value="v2.0.0")
        self.version_dropdown = ctk.CTkComboBox(
            self.version_frame,
            values=["v1.0.0", "v2.0.0", "dev"],
            variable=self.version_var,
            width=200
        )
        self.version_dropdown.pack(side="left", padx=10)
        
        # 进度条
        self.progress = ModernProgressBar(
            self.main_frame,
            mode='determinate'
        )
        self.progress.pack(fill="x", padx=30, pady=20)
        
        # 状态信息
        self.status_label = ctk.CTkLabel(
            self.main_frame,
            text="准备就绪",
            font=("Segoe UI", 12)
        )
        self.status_label.pack(pady=10)
        
        # 按钮区域
        self.button_frame = ctk.CTkFrame(self.main_frame)
        self.button_frame.pack(pady=20)
        
        self.deploy_btn = ctk.CTkButton(
            self.button_frame,
            text="启动部署",
            command=self.on_deploy,
            width=150,
            height=40,
            font=("Segoe UI", 14)
        )
        self.deploy_btn.pack(side="left", padx=10)
        
        # 控制器初始化
        self.controller = VersionController()
        self.start_backend()
        
    def update_status(self, text, is_error=False):
        color = "#ff0000" if is_error else "#00ff00"
        self.status_label.configure(text=text, text_color=color)
        
    def on_deploy(self):
        version = self.version_var.get()
        self.deploy_btn.configure(state="disabled")
        
        def deploy_thread():
            try:
                self.progress.start_progress(3.0)
                self.update_status("正在克隆仓库...")
                
                if self.controller.clone_version(version):
                    time.sleep(1)  # 给进度条一些时间
                    self.update_status("正在启动机器人...")
                    
                    if self.controller.start_bot(version):
                        self.update_status("部署完成！")
                    else:
                        self.update_status("启动失败", True)
                else:
                    self.update_status("部署失败", True)
                    
            finally:
                self.deploy_btn.configure(state="normal")
        
        threading.Thread(target=deploy_thread).start()
    
    def start_backend(self):
        def run_server():
            uvicorn.run(app, host="127.0.0.1", port=8000)
        threading.Thread(target=run_server, daemon=True).start()

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    app = App()
    app.mainloop()
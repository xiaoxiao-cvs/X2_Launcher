from tkinter import ttk
import customtkinter as ctk

# 自定义的现代进度条类，继承自ttk.Progressbar。
class ModernProgressBar(ttk.Progressbar):
    # 初始化现代进度条。
    def __init__(self, *args, **kwargs):
        # 调用父类的初始化方法。
        super().__init__(*args, **kwargs)
        # 配置进度条样式。
        self.configure(style="Modern.Horizontal.TProgressbar")
        
    # 开始进度条动画。
    def start_progress(self, duration=1.0):
        # 设置进度条初始值为0。
        self.configure(value=0)
        # 计算每次步进的大小。
        self.step_size = 100 / (duration * 10)
        # 更新进度条。
        self._update_progress()
        
    # 更新进度条值，当进度条值小于100时，继续增加进度条的值。
    def _update_progress(self):
        # 获取当前进度条的值。
        current = self['value']
        # 如果当前进度小于100，则继续增加进度。
        if current < 100:
            # 增加进度条的值。
            self.step(self.step_size)
            # 延迟100毫秒后再次更新进度条。
            self.after(100, self._update_progress)

# 设置窗口类，继承自customtkinter的CTkToplevel。
class SettingsWindow(ctk.CTkToplevel):
    # 初始化设置窗口。
    def __init__(self, parent):
        # 调用父类的初始化方法。
        super().__init__(parent)
        self.parent = parent
        # 设置窗口标题。
        self.title("设置")
        # 设置窗口大小。
        self.geometry("600x400")
        window_width = 600
        window_height = 400
        # 配置列权重。
        self.grid_columnconfigure(0, weight=1)
        # 配置行权重。
        self.grid_rowconfigure(0, weight=1)
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # 计算居中位置
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        # 窗口置顶
        self.transient(parent)  
        self.grab_set()
        # 设置窗口位置和大小
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 创建标签视图。
        self.tabview = ctk.CTkTabview(self)
        # 将标签视图放置在窗口中。
        self.tabview.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        # 添加“外观”标签页。
        self.tab_appearance = self.tabview.add("外观")
        # 添加“部署”标签页。
        self.tab_deployment = self.tabview.add("部署")
        
        # 初始化“外观”标签页。
        self.init_appearance_tab()
        # 初始化“部署”标签页。
        self.init_deployment_tab()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # 初始化外观设置标签页。
    def init_appearance_tab(self):
        # 创建外观设置框架
        appearance_frame = ctk.CTkFrame(self.tab_appearance)
        appearance_frame.pack(padx=10, pady=10, fill="both", expand=True)
        ctk.CTkLabel(
            appearance_frame, 
            text="主题模式:"
        ).pack(pady=(10, 0), anchor="w")
        self.theme_mode = ctk.StringVar(value="System")
        theme_options = ["Light", "Dark", "System"]
        # 主色调选择
        ctk.CTkLabel(
            appearance_frame, 
            text="主色调:"
        ).pack(pady=(10, 0), anchor="w")
        self.main_color = ctk.StringVar(value="#2b2b2b")
        color_options = ["#2b2b2b", "#1f6aa5", "#3a7ebf", "#5d9cec", "#44b78b"]
        color_menu = ctk.CTkOptionMenu(
            appearance_frame,
            values=color_options,
            variable=self.main_color,
            command=self.change_main_color
        )
        color_menu.pack(pady=5, fill="x")
        # 自定义颜色选择
        ctk.CTkLabel(
            appearance_frame, 
            text="自定义颜色:"
        ).pack(pady=(10, 0), anchor="w")
        self.color_picker = ctk.CTkButton(
            appearance_frame,
            text="选择颜色",
            command=self.pick_color
        )
        self.color_picker.pack(pady=5, fill="x")
        # 透明度调节滑块
        ctk.CTkLabel(
            appearance_frame, 
            text="透明度:"
        ).pack(pady=(10, 0), anchor="w")
        self.transparency = ctk.DoubleVar(value=0.9)
        transparency_slider = ctk.CTkSlider(
            appearance_frame,
            from_=0.5,
            to=1.0,
            number_of_steps=10,
            variable=self.transparency,
            command=self.change_transparency
        )
        transparency_slider.pack(pady=5, fill="x")
        # 应用按钮
        apply_button = ctk.CTkButton(
            appearance_frame,
            text="应用设置",
            command=self.apply_appearance_settings
        )
        apply_button.pack(pady=20, fill="x")
        pass

    # 初始化部署设置标签页。
    def init_deployment_tab(self):
        # 实现部署设置页面
        pass
    def on_close(self):
        """窗口关闭时的处理"""
        # 清除父窗口对当前窗口的引用
        self.parent.settings_window = None
        self.destroy()
    def change_theme(self, new_theme):
        """更改主题模式"""
        ctk.set_appearance_mode(new_theme)
        self.parent.settings.set("appearance", "theme_mode", new_theme)
    def change_main_color(self, new_color):
        """更改主色调"""
        ctk.set_default_color_theme(new_color)
        self.parent.settings.set("appearance", "main_color", new_color)
    def pick_color(self):
        """打开颜色选择器"""
        color = ctk.CTkColorPicker.ask_color()
        if color:
            self.main_color.set(color)
            self.change_main_color(color)
    def change_transparency(self, value):
        """更改透明度"""
        try:
            if hasattr(self.parent, '_set_ui_transparency'):
                self.parent._set_ui_transparency(float(value))
            else:
                print("父窗口缺少透明度控制方法")
        except Exception as e:
            if hasattr(self.parent, 'log_message'):
                self.parent.log_message(f"透明度设置错误: {str(e)}", "ERROR")
            # 同时显示错误提示窗口
            SuccessWindow(self, f"透明度设置失败: {str(e)}")
    def apply_appearance_settings(self):
        """应用所有外观设置"""
        self.parent.settings.save()
        success_window = SuccessWindow(self, "外观设置已应用")
        success_window.focus()
class SuccessWindow(ctk.CTkToplevel):
    """自定义成功提示窗口"""
    def __init__(self, parent, message):
        super().__init__(parent)
        self.title("提示")
        
        # 设置窗口大小和居中
        window_width = 300
        window_height = 150
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 窗口置顶属性
        self.attributes('-topmost', True)
        self.transient(parent)
        self.grab_set()
        
        # 内容布局
        ctk.CTkLabel(
            self,
            text=message,
            font=("Arial", 14)
        ).pack(pady=20)
        
        ctk.CTkButton(
            self,
            text="确定",
            command=self.destroy
        ).pack(pady=10)
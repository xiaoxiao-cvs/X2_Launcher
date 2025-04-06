import customtkinter as ctk
from tkinter import messagebox

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("𝕏² Deploy Station")
        self.geometry("400x200")
        
        # 版本选择组件
        self.version_label = ctk.CTkLabel(self, text="选择麦麦版本：")
        self.version_label.pack(pady=10)
        
        self.version_var = ctk.StringVar(value="v2.0.0")
        self.version_dropdown = ctk.CTkComboBox(
            self,
            values=["v1.0.0", "v2.0.0", "dev"],
            variable=self.version_var
        )
        self.version_dropdown.pack()
        
        # 部署按钮
        self.deploy_btn = ctk.CTkButton(
            self,
            text="启动量子部署",
            command=self.on_deploy
        )
        self.deploy_btn.pack(pady=20)
    
    def on_deploy(self):
        selected = self.version_var.get()
        messagebox.showinfo(
            "部署启动", 
            f"正在折叠时空到 {selected} 分支..."
        )

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    app = App()
    app.mainloop()
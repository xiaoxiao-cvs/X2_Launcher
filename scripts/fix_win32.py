import os
import sys
import subprocess
import winreg
import platform

def fix_win32():
    """修复win32模块"""
    print("开始修复win32模块...")
    
    # 1. 获取Python路径
    python_path = sys.executable
    python_dir = os.path.dirname(python_path)
    site_packages = os.path.join(python_dir, 'Lib', 'site-packages')
    
    print(f"Python路径: {python_path}")
    print(f"site-packages: {site_packages}")
    
    # 2. 重新安装pywin32
    try:
        subprocess.run([
            python_path, "-m", "pip", "install",
            "--force-reinstall",
            "--no-cache-dir",
            "pywin32==310"
        ], check=True)
        print("pywin32重新安装完成")
    except Exception as e:
        print(f"安装失败: {e}")
        return
    
    # 3. 运行post install脚本
    try:
        win32_path = os.path.join(site_packages, 'win32')
        if os.path.exists(win32_path):
            sys.path.append(win32_path)
            print("已添加win32路径到系统路径")
            
            # 运行postinstall脚本
            postinstall = os.path.join(site_packages, 'pywin32_system32', 'scripts', 'pywin32_postinstall.py')
            if os.path.exists(postinstall):
                subprocess.run([python_path, postinstall, "-install"], check=True)
                print("post install脚本执行完成")
            else:
                print(f"未找到post install脚本: {postinstall}")
    except Exception as e:
        print(f"post install失败: {e}")

if __name__ == "__main__":
    if platform.system() != 'Windows':
        print("此脚本仅支持Windows系统")
        sys.exit(1)
    fix_win32()

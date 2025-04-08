import os
import sys
import subprocess
import platform

def fix_pywin32():
    """修复pywin32安装"""
    if platform.system() != 'Windows':
        print("这个脚本只能在Windows系统上运行")
        return
        
    try:
        # 1. 卸载现有pywin32
        subprocess.run([
            sys.executable,
            "-m", "pip", "uninstall", "-y", "pywin32"
        ], check=True)
        
        # 2. 重新安装指定版本
        subprocess.run([
            sys.executable,
            "-m", "pip", "install",
            "--force-reinstall",
            "--no-cache-dir",
            "pywin32==306"
        ], check=True)
        
        # 3. 运行post install脚本
        try:
            import pythoncom
            script_path = os.path.join(os.path.dirname(pythoncom.__file__), "Scripts", "pywin32_postinstall.py")
            if os.path.exists(script_path):
                subprocess.run([sys.executable, script_path, "-install"], check=True)
                print("pywin32修复完成")
            else:
                print("警告: 未找到post install脚本")
        except ImportError:
            print("警告: 无法导入pythoncom，请手动运行post install脚本")
            
    except subprocess.CalledProcessError as e:
        print(f"修复过程出错: {e}")
    except Exception as e:
        print(f"发生未知错误: {e}")

if __name__ == "__main__":
    fix_pywin32()

# -*- coding: utf-8 -*-
"""
后端诊断工具
用于诊断和修复启动问题
"""
import os
import sys
import importlib
import traceback

# 首先确保编码正确
try:
    from utils.encoding_fix import encoding_fixed
    if not encoding_fixed:
        print("警告：编码修复失败，可能会出现中文问题")
except ImportError:
    print("警告：无法导入编码修复模块")

def check_module(module_name):
    """检查模块是否可以导入"""
    try:
        importlib.import_module(module_name)
        return True, None
    except ImportError as e:
        return False, str(e)
    except Exception as e:
        return False, f"加载时错误: {str(e)}"

def run_diagnostics():
    """运行诊断检查"""
    print("\n===== 后端启动诊断 =====")
    
    # 检查Python版本
    print(f"Python版本: {sys.version}")
    
    # 检查工作目录
    print(f"工作目录: {os.getcwd()}")
    
    # 检查必需模块
    required_modules = [
        'fastapi', 'uvicorn', 'pydantic', 
        'websockets', 'aiofiles', 'psutil', 
        'packaging'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        success, error = check_module(module)
        status = "✓" if success else "✗"
        if not success:
            missing_modules.append((module, error))
        print(f"{status} {module}")
    
    # 如果有缺失模块，打印安装命令
    if missing_modules:
        print("\n缺失以下模块:")
        for module, error in missing_modules:
            print(f"  - {module}: {error}")
        
        modules_str = " ".join([m[0] for m in missing_modules])
        print(f"\n请执行以下命令安装缺失模块:")
        print(f"pip install {modules_str}")
    
    # 检查主程序导入
    print("\n尝试导入主模块...")
    try:
        from main import app
        print("主应用导入成功")
    except Exception as e:
        print(f"导入主应用失败:\n{str(e)}")
        print("\n详细错误信息:")
        traceback.print_exc()
        
    print("\n===== 诊断完成 =====")

if __name__ == "__main__":
    run_diagnostics()

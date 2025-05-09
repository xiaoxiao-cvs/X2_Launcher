# -*- coding: utf-8 -*-
"""
处理Python编码问题，确保正确支持中文
"""
import os
import sys
import locale

# 用于跟踪是否修复成功
encoding_fixed = False

try:
    # 设置控制台编码为UTF-8
    if sys.platform == "win32":
        # Windows平台
        import ctypes
        
        # 尝试设置控制台代码页为UTF-8 (Code Page 65001)
        try:
            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
            ctypes.windll.kernel32.SetConsoleCP(65001)
        except Exception as e:
            print(f"设置控制台代码页失败: {e}")
    
    # 设置环境变量
    os.environ["PYTHONIOENCODING"] = "utf-8"
    
    # 检查编码设置
    console_encoding = sys.stdout.encoding
    python_encoding = sys.getdefaultencoding()
    locale_encoding = locale.getpreferredencoding()
    
    # 验证编码是否为UTF-8
    if console_encoding.lower() == 'utf-8' and python_encoding.lower() == 'utf-8':
        encoding_fixed = True
    
    if not encoding_fixed:
        print(f"警告: 编码可能不是UTF-8")
        print(f"控制台编码: {console_encoding}")
        print(f"Python默认编码: {python_encoding}")
        print(f"系统首选编码: {locale_encoding}")
    
except Exception as e:
    print(f"编码修复失败: {e}")

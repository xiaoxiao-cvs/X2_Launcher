# -*- coding: utf-8 -*-
"""
处理Python编码问题，确保正确支持中文
"""
import os
import sys
import locale
import io

# 用于跟踪是否修复成功
encoding_fixed = False

def fix_encoding():
    """应用编码修复"""
    global encoding_fixed
    
    try:
        # 强制设置环境变量
        os.environ["PYTHONIOENCODING"] = "utf-8"
        
        # 标准输出/错误流重定向为UTF-8
        if sys.stdout.encoding != 'utf-8':
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        if sys.stderr.encoding != 'utf-8':
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
            
        # Windows平台特殊处理
        if sys.platform == "win32":
            import ctypes
            
            # 设置控制台代码页为UTF-8 (Code Page 65001)
            try:
                ctypes.windll.kernel32.SetConsoleOutputCP(65001)
                ctypes.windll.kernel32.SetConsoleCP(65001)
                
                # 对于某些Windows环境，可能需要额外处理
                if sys.version_info >= (3, 6):
                    os.system("")  # 激活VT100模式，支持ANSI颜色
            except Exception as e:
                print(f"设置Windows控制台代码页失败: {e}")
        
        # 检查编码设置
        console_encoding = sys.stdout.encoding
        python_encoding = sys.getdefaultencoding()
        locale_encoding = locale.getpreferredencoding()
        
        # 打印编码信息（调试用）
        #print(f"控制台编码: {console_encoding}")
        #print(f"Python默认编码: {python_encoding}")
        #print(f"系统首选编码: {locale_encoding}")
        
        # 验证编码是否为UTF-8
        if console_encoding and console_encoding.lower() == 'utf-8' and python_encoding.lower() == 'utf-8':
            encoding_fixed = True
            return True
        
        if not encoding_fixed:
            print(f"警告: 编码可能不是UTF-8")
            print(f"控制台编码: {console_encoding}")
            print(f"Python默认编码: {python_encoding}")
            print(f"系统首选编码: {locale_encoding}")
            print("尝试中文输出测试: 你好，世界！")
    
    except Exception as e:
        print(f"编码修复失败: {e}")
        import traceback
        traceback.print_exc()
    
    return encoding_fixed

# 自动应用编码修复
is_fixed = fix_encoding()

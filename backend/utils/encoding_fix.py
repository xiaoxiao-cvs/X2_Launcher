# -*- coding: utf-8 -*-
"""
修复Windows下的编码问题，确保能正确处理中文
"""
import os
import sys
import locale

# 标记是否成功修复编码
encoding_fixed = False

try:
    # 检查当前编码
    current_encoding = locale.getpreferredencoding()
    print(f"当前系统编码: {current_encoding}")
    
    # 修正环境变量编码
    if sys.platform == 'win32':
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        
        # 如果不是utf-8，尝试修复
        if current_encoding.upper() != 'UTF-8':
            # 尝试设置控制台编码
            os.system('chcp 65001 > nul')
            print("已尝试将控制台编码设置为UTF-8 (CP65001)")
            
            # 设置输出编码
            if sys.stdout.encoding != 'utf-8':
                if hasattr(sys.stdout, 'reconfigure'):
                    sys.stdout.reconfigure(encoding='utf-8')
                    print("已重配置标准输出为UTF-8")
                else:
                    print("警告：无法重配置输出流编码")
            
            # 设置输入编码
            if sys.stdin.encoding != 'utf-8':
                if hasattr(sys.stdin, 'reconfigure'):
                    sys.stdin.reconfigure(encoding='utf-8')
    
    # 验证是否设置成功
    if sys.stdout.encoding.upper() == 'UTF-8':
        encoding_fixed = True
        print("编码修正成功：现在使用UTF-8")
    else:
        print(f"注意：输出编码仍为 {sys.stdout.encoding}，可能会有中文显示问题")
    
except Exception as e:
    print(f"编码修复失败: {e}")

# -*- coding: utf-8 -*-
"""
X2 Launcher 后端诊断工具
提供全面的系统环境检查和问题解决建议
"""
import os
import sys
import importlib
import platform
import subprocess
import traceback
from pathlib import Path
import urllib.request
import json

# 设置颜色代码
if sys.platform == 'win32':
    # Windows颜色
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    
    # 在Windows中启用ANSI颜色支持
    os.system('color')
else:
    # Unix颜色
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def print_header(message):
    """打印带格式的标题"""
    line = "=" * len(message)
    print(f"\n{BLUE}{BOLD}{line}{RESET}")
    print(f"{BLUE}{BOLD}{message}{RESET}")
    print(f"{BLUE}{BOLD}{line}{RESET}")

def print_status(message, success=True):
    """打印状态消息"""
    status = f"{GREEN}✓{RESET}" if success else f"{RED}✗{RESET}"
    print(f"{status} {message}")

def print_warning(message):
    """打印警告消息"""
    print(f"{YELLOW}⚠ {message}{RESET}")

def print_info(message):
    """打印信息消息"""
    print(f"{BLUE}ℹ {message}{RESET}")

def check_module(module_name):
    """检查模块是否可以导入"""
    try:
        importlib.import_module(module_name)
        return True, None
    except ImportError as e:
        return False, str(e)
    except Exception as e:
        return False, f"加载时错误: {str(e)}"

def check_system_env():
    """检查系统环境"""
    print_header("系统环境检查")
    
    # 检查Python版本
    python_version = platform.python_version()
    is_python_valid = tuple(map(int, python_version.split('.'))) >= (3, 8)
    print_status(f"Python版本: {python_version}", is_python_valid)
    if not is_python_valid:
        print_warning("Python版本过低，推荐使用 Python 3.8 或更高版本")
    
    # 检查操作系统
    os_name = platform.system()
    os_version = platform.version()
    print_status(f"操作系统: {os_name} {os_version}", True)
    
    # 检查编码设置
    encoding = sys.getdefaultencoding()
    is_encoding_valid = encoding.lower() == 'utf-8'
    print_status(f"默认编码: {encoding}", is_encoding_valid)
    if not is_encoding_valid:
        print_warning("默认编码不是UTF-8，可能会导致中文显示问题")

def check_required_modules():
    """检查必要的Python模块"""
    print_header("必要模块检查")
    
    required_modules = {
        'fastapi': '0.95.0',
        'uvicorn': '0.21.0',
        'pydantic': '1.10.0',
        'websockets': '11.0.0',
        'aiofiles': '23.1.0',
        'psutil': '5.9.0',
        'packaging': '23.0'
    }
    
    missing_modules = []
    outdated_modules = []
    
    for module, min_version in required_modules.items():
        success, error = check_module(module)
        if success:
            # 检查版本
            try:
                mod = importlib.import_module(module)
                version = getattr(mod, '__version__', '未知')
                
                # 输出版本信息
                print_status(f"{module}: {version}", True)
                
                # 检查版本是否过低
                if version != '未知' and version < min_version:
                    outdated_modules.append((module, version, min_version))
            except Exception:
                print_status(f"{module}: 已安装但无法获取版本", True)
        else:
            print_status(f"{module}: {error}", False)
            missing_modules.append(module)
    
    if missing_modules:
        print_warning("\n缺少以下模块:")
        modules_str = " ".join(missing_modules)
        print(f"  pip install {modules_str}")
    
    if outdated_modules:
        print_warning("\n以下模块需要更新:")
        for module, current, required in outdated_modules:
            print(f"  {module}: {current} -> {required}")
        print("\n可以使用以下命令更新:")
        print(f"  pip install --upgrade {' '.join([m[0] for m in outdated_modules])}")

def check_file_structure():
    """检查文件结构"""
    print_header("文件结构检查")
    
    # 必要的文件和目录
    required_files = [
        "main.py",
        "routes",
        "routes/api.py",
        "routes/deploy.py",
        "routes/websocket.py",
        "services",
        "services/system_info.py",
        "services/instance_manager.py"
    ]
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    all_exist = True
    
    for file_path in required_files:
        path = os.path.join(current_dir, file_path)
        exists = os.path.exists(path)
        print_status(file_path, exists)
        if not exists:
            all_exist = False
    
    if not all_exist:
        print_warning("一些必要的文件或目录不存在，可能需要完成项目结构")

def check_network_connectivity():
    """检查网络连接性"""
    print_header("网络连接检查")
    
    urls = [
        ("GitHub API", "https://api.github.com"),
        ("PyPI", "https://pypi.org"),
        ("清华镜像", "https://pypi.tuna.tsinghua.edu.cn")
    ]
    
    for name, url in urls:
        try:
            # 设置超时避免长时间等待
            response = urllib.request.urlopen(url, timeout=5)
            status = response.getcode()
            print_status(f"{name} ({url}): 状态码 {status}", status == 200)
        except Exception as e:
            print_status(f"{name} ({url}): 连接失败 - {str(e)}", False)

def test_import_app():
    """测试导入主应用"""
    print_header("主应用导入测试")
    
    try:
        from main import app
        print_status("成功导入主应用", True)
        
        # 检查路由是否已注册
        routes_count = len(app.routes)
        print_status(f"已注册 {routes_count} 个路由", routes_count > 0)
        
        return True
    except Exception as e:
        print_status("主应用导入失败", False)
        print_warning(f"错误详情: {str(e)}")
        traceback.print_exc()
        return False

def suggest_fixes(issues):
    """根据发现的问题提供修复建议"""
    if not issues:
        print_header("诊断完成")
        print_info("没有发现问题，系统应该可以正常运行")
        return

    print_header("修复建议")
    
    for issue in issues:
        if issue == "missing_modules":
            print_info("请安装缺少的模块后再尝试启动")
        elif issue == "python_version":
            print_info("请更新Python版本至少到3.8以上")
        elif issue == "file_structure":
            print_info("创建缺少的文件并完善项目结构")
        elif issue == "encoding":
            print_info("在启动脚本中添加 os.environ[\"PYTHONIOENCODING\"] = \"utf-8\"")
    
    print("\n如果问题仍然存在，请查看详细的错误日志或联系支持人员。")

def run_full_diagnostics():
    """运行全面诊断"""
    # 打印系统标识
    print(f"\n{BLUE}{BOLD}===== X² Launcher 后端启动诊断 ====={RESET}")
    print(f"当前时间: {platform.strftime('%Y-%m-%d %H:%M:%S', platform.localtime())}\n")
    
    # 收集问题
    issues = []
    
    # 系统环境检查
    check_system_env()
    # Python编码检查
    if sys.getdefaultencoding().lower() != 'utf-8':
        issues.append("encoding")
    
    # Python版本检查
    py_version = tuple(map(int, platform.python_version().split('.')))
    if py_version < (3, 8):
        issues.append("python_version")
    
    # 必要模块检查
    check_required_modules()
    
    # 文件结构检查
    check_file_structure()
    
    # 网络连接检查
    check_network_connectivity()
    
    # 导入测试
    app_imported = test_import_app()
    if not app_imported:
        issues.append("import_error")
    
    # 提供修复建议
    suggest_fixes(issues)
    
    return len(issues) == 0

if __name__ == "__main__":
    # 设置编码
    os.environ["PYTHONIOENCODING"] = "utf-8"
    
    try:
        success = run_full_diagnostics()
        
        if success:
            print(f"\n{GREEN}诊断完成，未发现严重问题，可以尝试启动服务{RESET}")
            print("运行命令: python main.py")
        else:
            print(f"\n{YELLOW}诊断发现一些问题，请解决后再尝试启动服务{RESET}")
            
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n诊断被用户中断")
        sys.exit(130)  # 标准中断退出码
    except Exception as e:
        print(f"\n{RED}诊断过程中出现错误: {e}{RESET}")
        traceback.print_exc()
        sys.exit(1)

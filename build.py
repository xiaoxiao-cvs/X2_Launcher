import subprocess
import shutil
import os
import sys
from pathlib import Path
from PIL import Image

def ensure_directory(path):
    """确保目录存在"""
    if not os.path.exists(path):
        os.makedirs(path)

def convert_to_ico():
    jpg_path = "assets/1.jpg"
    ico_path = "assets/app.ico"
    
    if not os.path.exists("assets"):
        os.makedirs("assets")
        
    if os.path.exists(jpg_path):
        try:
            # 转换图片为ico
            with Image.open(jpg_path) as img:
                # 确保尺寸适合图标
                img = img.resize((256, 256))
                img.save(ico_path, format='ICO')
            return ico_path
        except Exception as e:
            print(f"图片转换失败: {str(e)}")
    return None

def install_pyinstaller():
    """安装PyInstaller"""
    print("正在安装PyInstaller...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install",
            "--index-url", "https://pypi.tuna.tsinghua.edu.cn/simple",
            "pyinstaller"
        ], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"PyInstaller安装失败: {e}")
        return False

def install_basic_deps(python_path):
    """在虚拟环境中安装基本依赖"""
    print("正在安装基本依赖...")
    try:
        # 升级pip
        subprocess.run([
            python_path, "-m", "pip", "install",
            "--upgrade", "pip",
            "--index-url", "https://pypi.tuna.tsinghua.edu.cn/simple"
        ], check=True)
        
        # 使用wheel安装pillow
        print("安装Pillow...")
        subprocess.run([
            python_path, "-m", "pip", "install",
            "--index-url", "https://pypi.tuna.tsinghua.edu.cn/simple",
            "--only-binary=:all:",  # 只使用预编译的wheel包
            "pillow>=9.5.0"  # 使用更稳定的版本
        ], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"基本依赖安装失败: {e}")
        return False

def install_dependencies():
    """分步安装依赖"""
    print("开始安装依赖...")
    
    # 先升级pip
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "--upgrade", "pip",
            "--index-url", "https://pypi.tuna.tsinghua.edu.cn/simple"
        ], check=True)
    except subprocess.CalledProcessError:
        print("pip升级失败，继续安装其他依赖...")
    
    # 分开安装核心依赖
    core_dependencies = {
        "PyInstaller": "6.12.0",  # 更新到最新稳定版本
        "customtkinter": "5.2.2",
        "uvicorn": "0.27.1",
        "fastapi": "0.109.0"
    }
    
    for dep, version in core_dependencies.items():
        try:
            print(f"正在安装 {dep} {version}...")
            subprocess.run([
                sys.executable, "-m", "pip", "install",
                "--index-url", "https://pypi.tuna.tsinghua.edu.cn/simple",
                "--only-binary=:all:",  # 尽可能使用预编译包
                f"{dep}=={version}"
            ], check=True)
        except subprocess.CalledProcessError as e:
            print(f"{dep}安装失败: {e}")
            return False
            
    # 安装其他可能的依赖
    if os.path.exists("requirements.txt"):
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install",
                "-r", "requirements.txt",
                "--index-url", "https://pypi.tuna.tsinghua.edu.cn/simple"
            ], check=True)
        except subprocess.CalledProcessError as e:
            print(f"其他依赖安装失败: {e}")
            # 不中断构建，因为核心依赖已安装
            print("继续构建...")
            
    return True

def build_application():
    """构建应用程序"""
    print("准备开始构建...")
    
    # 确保PyInstaller已安装
    try:
        import PyInstaller.__main__
    except ImportError:
        if not install_pyinstaller():
            print("PyInstaller安装失败，退出构建")
            sys.exit(1)
        # 重新导入
        import PyInstaller.__main__
    
    print("开始构建应用...")
    ensure_directory('dist')
    
    # 转换图标
    ico_path = convert_to_ico()
    
    # 构建后端
    try:
        PyInstaller.__main__.run([
            'main.py',
            '--onefile',
            '--name=backend',
            '--hidden-import=uvicorn',
            '--hidden-import=fastapi',
            '--clean'
        ])
    except Exception as e:
        print(f"后端构建失败: {e}")
        sys.exit(1)
    
    # 构建启动器
    launcher_args = [
        'launcher.py',
        '--onefile',
        '--name=MaiBotDeployStation',
        '--noconsole',
        '--clean'
    ]
    
    # 如果存在图标则添加
    if os.path.exists('assets/app.ico'):
        launcher_args.extend(['--icon', 'assets/app.ico'])
    else:
        print("警告: 图标文件不存在，将使用默认图标")
    
    try:
        PyInstaller.__main__.run(launcher_args)
    except Exception as e:
        print(f"启动器构建失败: {e}")
        sys.exit(1)
    
    # 修改资源文件复制逻辑
    resources = [
        ('resources/python-3.13.0-amd64.exe', 'python-3.13.0-amd64.exe'),
        ('requirements.txt', 'requirements.txt'),
        ('config.json', 'config.json'),
        ('assets', 'assets')  # 复制整个assets目录
    ]
    
    print("正在复制资源文件...")
    for src, dst in resources:
        try:
            dst_path = os.path.join('dist', dst)
            if os.path.isdir(src):
                shutil.copytree(src, dst_path, dirs_exist_ok=True)
            elif os.path.exists(src):
                shutil.copy2(src, dst_path)
            else:
                print(f"警告: 资源文件不存在: {src}")
        except Exception as e:
            print(f"复制{src}失败: {e}")

def check_venv():
    """检查并创建虚拟环境"""
    venv_dir = '.venv'
    if not os.path.exists(venv_dir):
        print("创建新的虚拟环境...")
        try:
            # 使用python -m venv创建虚拟环境
            subprocess.run([
                sys.executable, "-m", "venv",
                "--clear", # 如果存在则清理
                venv_dir
            ], check=True)
            
            # 获取虚拟环境的python路径
            if os.name == 'nt':  # Windows
                python_path = os.path.join(os.getcwd(), venv_dir, 'Scripts', 'python.exe')
            else:  # Unix/Linux
                python_path = os.path.join(venv_dir, 'bin', 'python')
                
            python_path = os.path.normpath(python_path)  # 标准化路径
            
            if not os.path.exists(python_path):
                raise Exception(f"虚拟环境创建失败: {python_path} 不存在")
                
            print(f"使用Python路径: {python_path}")
            return python_path
        except Exception as e:
            print(f"虚拟环境创建失败: {e}")
            return None
    else:
        if os.name == 'nt':
            python_path = os.path.join(os.getcwd(), venv_dir, 'Scripts', 'python.exe')
        else:
            python_path = os.path.join(venv_dir, 'bin', 'python')
        python_path = os.path.normpath(python_path)
        return python_path

if __name__ == "__main__":
    try:
        # 检查并创建虚拟环境
        python_path = check_venv()
        if not python_path:
            print("无法创建或找到虚拟环境，退出构建")
            sys.exit(1)
            
        # 使用虚拟环境的Python安装依赖
        if not install_basic_deps(python_path):
            print("基本依赖安装失败，退出构建")
            sys.exit(1)
            
        # 确保已安装 uvicorn 和 fastapi
        if not install_dependencies():
            print("依赖安装失败，退出构建")
            sys.exit(1)
            
        build_application()
        print("构建完成!")
    except KeyboardInterrupt:
        print("\n构建被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"构建过程出现错误: {e}")
        sys.exit(1)

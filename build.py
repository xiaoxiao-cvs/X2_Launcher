import PyInstaller.__main__
import shutil
import os
import sys
from PIL import Image

def ensure_directory(path):
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

def build_application():
    ensure_directory('dist')
    
    # 转换图标
    ico_path = convert_to_ico()
    
    # 打包参数
    args = [
        'main.py',
        '--onefile',
        '--name=backend',
        '--hidden-import=uvicorn',
        '--hidden-import=fastapi',
    ]
    
    # 添加图标参数（如果转换成功）
    if ico_path and os.path.exists(ico_path):
        args.extend(['--icon', ico_path])
    
    # 打包后端
    PyInstaller.__main__.run(args)
    
    # 复制必要文件到dist
    if os.path.exists('resources/python-3.13.0-amd64.exe'):
        shutil.copy('resources/python-3.13.0-amd64.exe', 'dist/python-3.13.0-amd64.exe')
    
    if os.path.exists('requirements.txt'):
        shutil.copy('requirements.txt', 'dist/requirements.txt')

if __name__ == "__main__":
    build_application()

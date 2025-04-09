#!/usr/bin/env python3
"""
NoneBot适配器安装脚本
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(cmd, cwd=None):
    """运行命令并打印输出"""
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        shell=True,
        cwd=cwd
    )
    
    for line in process.stdout:
        print(line.strip())
    
    process.wait()
    return process.returncode


def setup_nonebot_adapter(base_dir):
    """安装NoneBot适配器"""
    print("开始安装NoneBot适配器...")
    
    # 确保基础目录存在
    base_dir = Path(base_dir)
    if not base_dir.exists():
        print(f"错误: 目录 {base_dir} 不存在")
        return False
    
    # 激活虚拟环境
    venv_dir = base_dir / "venv"
    venv_activate = venv_dir / "Scripts" / "activate.bat" if sys.platform == "win32" else venv_dir / "bin" / "activate"
    
    if not venv_activate.exists():
        print(f"错误: 虚拟环境不存在 {venv_activate}")
        return False
    
    try:
        # 创建NoneBot项目
        adapter_dir = base_dir / "nonebot-maibot-adapter"
        if adapter_dir.exists():
            print(f"NoneBot适配器目录已存在: {adapter_dir}")
            # 可以选择更新现有适配器
            return True
        
        print("使用nb-cli创建NoneBot项目...")
        os.chdir(base_dir)
        
        if sys.platform == "win32":
            cmd = f'"{venv_activate}" && nb create'
            process = subprocess.Popen(cmd, shell=True)
            process.wait()
            
            if process.returncode != 0:
                print("创建NoneBot项目失败")
                return False
        else:
            cmd = f'source "{venv_activate}" && nb create'
            os.system(cmd)
        
        # 检查目录是否创建成功
        if not adapter_dir.exists():
            print("找不到创建的NoneBot项目目录，请检查nb create的输出信息")
            adapter_dirs = [d for d in base_dir.iterdir() if d.is_dir() and d.name.startswith("nonebot")]
            if adapter_dirs:
                print(f"找到可能的NoneBot目录: {adapter_dirs[0]}")
                adapter_dir = adapter_dirs[0]
                
                # 重命名为标准名称
                try:
                    shutil.move(str(adapter_dirs[0]), str(base_dir / "nonebot-maibot-adapter"))
                    adapter_dir = base_dir / "nonebot-maibot-adapter"
                    print(f"已将目录重命名为: {adapter_dir}")
                except Exception as e:
                    print(f"重命名目录时出错: {e}")
            else:
                return False
        
        # 克隆适配器插件
        adapters_dir = adapter_dir / "src" / "plugins"
        if not adapters_dir.exists():
            adapters_dir.mkdir(parents=True, exist_ok=True)
        
        os.chdir(base_dir)
        print("正在克隆MaiBot适配器插件...")
        
        if not (base_dir / "nonebot-plugin-maibot-adapters").exists():
            run_command("git clone https://github.com/Maple127667/nonebot-plugin-maibot-adapters.git", cwd=str(base_dir))
        
        # 复制适配器到NoneBot项目
        src_adapter = base_dir / "nonebot-plugin-maibot-adapters" / "nonebot_plugin_maibot_adapters"
        dest_adapter = adapters_dir / "nonebot_plugin_maibot_adapters"
        
        if src_adapter.exists():
            print(f"正在将适配器复制到 {dest_adapter}")
            if dest_adapter.exists():
                shutil.rmtree(dest_adapter)
            shutil.copytree(src_adapter, dest_adapter)
        else:
            print(f"错误: 找不到适配器源目录 {src_adapter}")
            return False
        
        # 创建.env配置文件
        env_file = adapter_dir / ".env"
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write("""ENVIRONMENT=dev
DRIVER=~fastapi+websockets
PORT=18002
HOST=0.0.0.0
ONEBOT_WS_URLS=["ws://127.0.0.1:8095"]
""")
        
        print("NoneBot适配器安装完成!")
        return True
        
    except Exception as e:
        print(f"安装NoneBot适配器时出错: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        base_dir = sys.argv[1]
    else:
        base_dir = os.getcwd()
    
    success = setup_nonebot_adapter(base_dir)
    sys.exit(0 if success else 1)

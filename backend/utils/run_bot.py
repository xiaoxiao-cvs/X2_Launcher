#!/usr/bin/env python3
"""
MaiBot 启动脚本
启动顺序: NapCat -> NoneBot -> MaiBot
"""

import os
import sys
import time
import argparse
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description='MaiBot启动工具')
    parser.add_argument('--napcat', action='store_true', help='启动NapCat')
    parser.add_argument('--nonebot', action='store_true', help='启动NoneBot适配器')
    parser.add_argument('--maibot', action='store_true', help='启动MaiBot')
    parser.add_argument('--all', action='store_true', help='启动所有组件')
    parser.add_argument('--napcat-port', type=int, default=8095, help='设置NapCat端口')
    parser.add_argument('--nonebot-port', type=int, default=18002, help='设置NoneBot端口')
    parser.add_argument('--maibot-port', type=int, default=8000, help='设置MaiBot端口')
    
    args = parser.parse_args()
    
    # 获取当前目录
    base_path = Path(os.getcwd())
    
    # 激活虚拟环境
    venv_activate = base_path / "venv" / "Scripts" / "activate.bat"
    if not venv_activate.exists():
        print("未找到虚拟环境，请先安装")
        return 1
    
    # 如果没有指定任何组件，启动所有
    if not (args.napcat or args.nonebot or args.maibot):
        args.all = True
    
    # 启动NapCat
    if args.napcat or args.all:
        print(f"正在启动NapCat (端口: {args.napcat_port})...")
        napcat_exe = base_path / "napcat" / "NapCat QQ.exe"
        if napcat_exe.exists():
            subprocess.Popen([str(napcat_exe)], cwd=str(base_path / "napcat"))
            print("NapCat已启动，请打开界面手动登录QQ")
            time.sleep(1)
        else:
            print(f"错误: 找不到NapCat程序 {napcat_exe}")
            if args.all:
                return 1
    
    # 启动NoneBot适配器
    if args.nonebot or args.all:
        print(f"正在启动NoneBot适配器 (端口: {args.nonebot_port})...")
        nonebot_dir = base_path / "nonebot-maibot-adapter"
        if nonebot_dir.exists():
            # 更新配置
            env_file = nonebot_dir / ".env"
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(f"""ENVIRONMENT=dev
DRIVER=~fastapi+websockets
PORT={args.nonebot_port}
HOST=0.0.0.0
ONEBOT_WS_URLS=["ws://127.0.0.1:{args.napcat_port}"]
""")
            
            # 启动NoneBot
            cmd = f'start cmd /k "cd {nonebot_dir} && "{venv_activate}" && nb run"'
            os.system(cmd)
            print(f"NoneBot适配器已启动，正在监听端口 {args.nonebot_port}")
            time.sleep(2)
        else:
            print(f"错误: 找不到NoneBot目录 {nonebot_dir}")
            if args.all:
                return 1
    
    # 启动MaiBot
    if args.maibot or args.all:
        print(f"正在启动MaiBot (端口: {args.maibot_port})...")
        maibot_dir = base_path / "MaiBot"
        if maibot_dir.exists():
            # 更新环境变量
            env_file = maibot_dir / ".env"
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(f"""ENVIRONMENT=dev
PORT={args.maibot_port}
""")
            
            # 启动MaiBot
            cmd = f'start cmd /k "cd {maibot_dir} && "{venv_activate}" && python main.py"'
            os.system(cmd)
            print(f"MaiBot已启动，正在监听端口 {args.maibot_port}")
        else:
            print(f"错误: 找不到MaiBot目录 {maibot_dir}")
            if args.all:
                return 1
    
    print("\n所有组件已启动，请不要关闭这个窗口")
    print("启动顺序：NapCat -> NoneBot适配器 -> MaiBot")
    print("关闭顺序: 请按相反顺序关闭或直接关闭所有窗口")
    return 0


if __name__ == "__main__":
    sys.exit(main())

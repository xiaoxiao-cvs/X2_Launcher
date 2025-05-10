import os
import sys
import json
import subprocess
from pathlib import Path
from fastapi import APIRouter, HTTPException, Body
from git import Repo

router = APIRouter()

MAIBOT_VISION_DIR = "maibot_vision"
ADAPTER_REPO_URL = "https://github.com/MaiM-with-u/MaiBot-Napcat-Adapter.git"
MAIN_REPO_URL = "https://github.com/MaiM-with-u/MaiBot.git"

def create_or_update_config(instance_name: str, config_data: dict):
    """创建或更新实例的配置文件"""
    config_dir = Path(MAIBOT_VISION_DIR) / instance_name
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.json"
    
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=4, ensure_ascii=False)
    return config_path

def setup_virtual_environment(target_dir: str):
    """创建虚拟环境并安装依赖"""
    venv_dir = os.path.join(target_dir, "venv")
    if not os.path.exists(venv_dir):
        subprocess.check_call([sys.executable, "-m", "venv", venv_dir])
        print(f"Virtual environment created in {venv_dir}")
    
    pip_executable = os.path.join(venv_dir, "Scripts", "pip")
    requirements_path = os.path.join(target_dir, "requirements.txt")
    if os.path.exists(requirements_path):
        subprocess.check_call([pip_executable, "install", "-i", "https://mirrors.aliyun.com/pypi/simple", "-r", requirements_path, "--upgrade"])
        print(f"Dependencies installed for {target_dir}")

@router.post("/deploy")
async def deploy_instance(version: str = Body(...), instance_name: str = Body(...)):
    """
    部署实例，包括克隆仓库、创建虚拟环境、安装依赖和记录配置
    """
    try:
        # 模拟部署逻辑
        return {"success": True, "message": f"部署任务已启动: {version}, 实例名称: {instance_name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"部署失败: {str(e)}")

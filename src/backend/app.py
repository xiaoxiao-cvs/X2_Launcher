import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from ..version_manager import VersionController
from ..logger import XLogger as logger  # 更新logger导入

app = FastAPI()
controller = None  # 初始化为 None

def init_controller(config):
    global controller
    controller = VersionController(config)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # 允许Vue开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 仅在生产环境中加载静态文件
frontend_dist = Path("frontend/dist")
if frontend_dist.exists():
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")

@app.get("/api/versions")
async def get_versions():
    try:
        versions = controller.get_versions()
        return {"versions": versions, "status": "success"}
    except Exception as e:
        logger.log(f"获取版本列表失败: {e}", "ERROR")
        raise HTTPException(status_code=500, detail="获取版本列表失败")

@app.post("/api/deploy/{version}")
async def deploy_version(version: str):
    try:
        success = controller.clone_version(version)
        if success:
            return {"status": "success", "message": f"版本 {version} 部署成功"}
        raise HTTPException(status_code=500, detail="部署失败")
    except Exception as e:
        logger.log(f"部署失败: {e}", "ERROR")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/start/{version}")
async def start_bot(version: str):
    try:
        success = controller.start_bot(version)
        if success:
            return {"status": "success", "message": "机器人启动成功"}
        raise HTTPException(status_code=500, detail="启动失败")
    except Exception as e:
        logger.log(f"启动失败: {e}", "ERROR")
        raise HTTPException(status_code=500, detail=str(e))

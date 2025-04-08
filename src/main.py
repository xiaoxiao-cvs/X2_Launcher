import os
import sys
from pathlib import Path
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 确保项目根目录在Python路径中
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.auth import GitHubAuth
from src.logger import XLogger
from src.settings import AppConfig as Settings
from src.version_manager import VersionController

app = FastAPI()
settings = Settings()
config = Settings.load_config()
version_controller = VersionController(config)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/versions")
async def get_versions():
    return {"versions": version_controller.get_versions()}

@app.post("/api/deploy/{version}")
async def deploy_version(version: str):
    success = version_controller.clone_version(version)
    return {"success": success}

@app.post("/api/start/{version}")
async def start_bot(version: str):
    success = version_controller.start_bot(version)
    return {"success": success}

@app.post("/api/stop")
async def stop_bot():
    success = version_controller.stop_bot()
    return {"success": success}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

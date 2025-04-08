import os
import sys
from pathlib import Path
import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

# 确保项目根目录在Python路径中
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from src.utils import setup_environment, check_network
from src.auth import GitHubAuth
from src.logger import XLogger
from src.settings import AppConfig as Settings
from src.version_manager import VersionController

# 创建FastAPI应用
app = FastAPI()
settings = Settings()
config = Settings.load_config()  # 这里返回的是字典
version_controller = VersionController({
    "github_token": config.get("github_token"),
    "default_version": config.get("default_version", "latest")
})

# 配置CORS - 添加Electron支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "app://*", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载前端静态文件
frontend_path = BASE_DIR / "frontend" / "dist"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")

@app.get("/")
async def root():
    """根路由重定向到前端页面"""
    return RedirectResponse(url="/index.html")

@app.on_event("startup")
async def startup_event():
    """启动事件"""
    # 初始化环境
    await setup_environment()
    
    # GitHub token验证
    if not config.get('github_token'):
        XLogger.log("未设置GitHub Token，某些功能可能受限", "WARNING")
    else:
        auth = GitHubAuth(config['github_token'])
        if not await auth.verify_token():
            XLogger.log("GitHub Token验证失败", "ERROR")

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
    try:
        XLogger.log("启动后端服务...")
        uvicorn.run(app, host="127.0.0.1", port=8000)
    except KeyboardInterrupt:
        XLogger.log("服务被用户中断", "INFO")
    except Exception as e:
        XLogger.log(f"服务异常退出: {e}", "CRITICAL")
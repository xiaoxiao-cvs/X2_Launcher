from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.version_manager import VersionController

app = FastAPI()
controller = VersionController()

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
    versions = controller.get_versions()
    return {"versions": versions}

@app.post("/api/deploy/{version}")
async def deploy_version(version: str):
    success = controller.clone_version(version)
    if success:
        return {"status": "success", "message": f"版本 {version} 部署成功"}
    return {"status": "error", "message": "部署失败"}

@app.post("/api/start/{version}")
async def start_bot(version: str):
    success = controller.start_bot(version)
    if success:
        return {"status": "success", "message": "机器人启动成功"}
    return {"status": "error", "message": "启动失败"}

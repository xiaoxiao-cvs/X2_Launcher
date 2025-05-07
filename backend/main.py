import sys
from pathlib import Path
import asyncio
import json
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

# 确保项目根目录在Python路径中
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.utils.logger import XLogger
from backend.utils.settings import AppConfig as Settings
from backend.utils.version_manager import VersionController
from backend.utils.download_manager import DownloadManager
from backend.utils.install_manager import InstallManager
from backend.utils.dependency_checker import DependencyChecker

app = FastAPI()
settings = Settings()
config = settings.load_config() if callable(getattr(settings, 'load_config', None)) else {}
version_controller = VersionController(config)
download_manager = DownloadManager()
install_manager = InstallManager()
dependency_checker = DependencyChecker()

# WebSocket连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

    async def send_log(self, log_data: dict):
        await self.broadcast(json.dumps(log_data))

manager = ConnectionManager()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 模型定义
class FolderRequest(BaseModel):
    path: str
    
class DownloadRequest(BaseModel):
    url: str
    path: str
    type: str
    branch: str = ""

# 安装配置模型
class QQConfigRequest(BaseModel):
    qq_number: str
    install_napcat: bool = False
    install_nonebot: bool = False
    run_install_script: bool = False

# 安装依赖模型
class DependencyInstallRequest(BaseModel):
    packages: Optional[List[str]] = None

# 命令模型
class CommandRequest(BaseModel):
    command: str

# API端点定义
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

@app.get("/api/instances")
async def get_instances():
    instances = version_controller.get_installed_instances()
    return {"instances": instances}

@app.delete("/api/instance/{name}")
async def delete_instance(name: str):
    success = version_controller.delete_instance(name)
    return {"success": success}

@app.post("/api/update/{name}")
async def update_instance(name: str):
    success = version_controller.update_instance(name)
    return {"success": success}

@app.post("/api/open-folder")
async def open_folder(data: FolderRequest):
    success = version_controller.open_folder(data.path)
    return {"success": success}

@app.post("/api/open-path")
async def open_path(data: FolderRequest):
    success = version_controller.open_folder(data.path)
    return {"success": success}

@app.get("/api/select-folder")
async def select_folder():
    """选择文件夹 (简化实现)"""
    return {"path": str(Path.home() / "Downloads")}

@app.get("/api/logs/system")
async def get_system_logs():
    logs = await version_controller.get_system_logs()
    return {"logs": logs}

@app.get("/api/logs/instance/{name}")
async def get_instance_logs(name: str):
    logs = version_controller.get_instance_logs(name)
    return {"logs": logs}

# 下载管理API
@app.get("/api/downloads")
async def get_downloads():
    """获取所有下载任务"""
    try:
        downloads = download_manager.get_downloads()
        return {"downloads": downloads}
    except Exception as e:
        XLogger.log(f"获取下载任务列表失败: {str(e)}", "ERROR")
        raise HTTPException(status_code=500, detail=f"获取下载任务列表失败: {str(e)}")

@app.post("/api/downloads")
async def add_download(data: DownloadRequest):
    """添加下载任务"""
    try:
        task = download_manager.add_download(
            url=data.url,
            path=data.path,
            download_type=data.type,
            branch=data.branch
        )
        # 自动开始下载
        download_manager.start_download(task.id)
        return {"success": True, "id": task.id}
    except Exception as e:
        XLogger.log(f"添加下载任务失败: {str(e)}", "ERROR")
        return {"success": False, "message": str(e)}

@app.post("/api/downloads/{id}/start")
async def start_download(id: str):
    """开始下载任务"""
    try:
        success = download_manager.start_download(id)
        return {"success": success}
    except Exception as e:
        XLogger.log(f"开始下载任务失败: {str(e)}", "ERROR")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/downloads/{id}/pause")
async def pause_download(id: str):
    """暂停下载任务"""
    try:
        success = download_manager.pause_download(id)
        return {"success": success}
    except Exception as e:
        XLogger.log(f"暂停下载任务失败: {str(e)}", "ERROR")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/downloads/{id}")
async def delete_download(id: str):
    """删除下载任务"""
    try:
        success = download_manager.delete_download(id)
        return {"success": success}
    except Exception as e:
        XLogger.log(f"删除下载任务失败: {str(e)}", "ERROR")
        raise HTTPException(status_code=500, detail=str(e))

# 安装API
@app.post("/api/install/configure")
async def configure_qq_settings(data: QQConfigRequest):
    """配置QQ设置并安装相关组件"""
    try:
        results = {}
        
        XLogger.log(f"开始配置QQ {data.qq_number}...")
        
        # 验证QQ号
        if not install_manager.is_valid_qq(data.qq_number):
            return {"success": False, "message": "无效的QQ号，请输入纯数字"}
        
        # 运行安装脚本
        if data.run_install_script:
            script_success = install_manager.run_install_script()
            results["install_script"] = script_success
            if not script_success:
                return {"success": False, "message": "安装脚本执行失败", "results": results}
        
        # 安装NoneBot
        if data.install_nonebot:
            nonebot_success = await install_manager.install_nonebot(data.qq_number)
            results["nonebot"] = nonebot_success
        
        # 安装NapCat
        if data.install_napcat:
            napcat_success = await install_manager.install_napcat(data.qq_number)
            results["napcat"] = napcat_success
            
        overall_success = all(results.values()) if results else True
        message = "配置完成" if overall_success else "部分配置失败，请检查日志"
        
        return {"success": overall_success, "message": message, "results": results}
    except Exception as e:
        XLogger.log(f"配置QQ设置失败: {str(e)}", "ERROR")
        return {"success": False, "message": str(e)}

@app.get("/api/install/status")
async def get_install_status():
    """获取安装状态"""
    try:
        status = {
            "napcat_installing": install_manager.napcat_installing,
            "nonebot_installing": install_manager.nonebot_installing
        }
        
        # 检查是否有Python进程在运行
        python_running = False
        try:
            # 检查是否有Python进程在运行安装脚本
            import psutil
            for proc in psutil.process_iter(['name', 'cmdline']):
                try:
                    pinfo = proc.info()
                    if 'python' in pinfo['name'].lower() and pinfo['cmdline'] and 'pip' in ' '.join(pinfo['cmdline']).lower():
                        python_running = True
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
        except ImportError:
            # 如果无法导入psutil，则依赖install_manager的状态
            pass
        
        status["python_installing"] = python_running
        status["installing"] = python_running or status["napcat_installing"] or status["nonebot_installing"]
        
        return status
    except Exception as e:
        XLogger.log(f"获取安装状态失败: {e}", "ERROR")
        return {"napcat_installing": False, "nonebot_installing": False, "python_installing": False, "installing": False}

# 依赖检查API
@app.get("/api/check-dependencies")
async def check_dependencies():
    """检查所有依赖库的安装情况"""
    try:
        result = dependency_checker.check_all_dependencies()
        return {"success": True, "results": result}
    except Exception as e:
        XLogger.log(f"依赖检查失败: {str(e)}", "ERROR")
        return {"success": False, "message": str(e)}

@app.post("/api/install-dependencies")
async def install_dependencies(data: DependencyInstallRequest = None):
    """安装所有缺失的必要依赖"""
    try:
        packages = data.packages if data and data.packages else None
        result = dependency_checker.install_missing_dependencies(packages)
        return {"success": result["overall_success"], "results": result["details"]}
    except Exception as e:
        XLogger.log(f"依赖安装失败: {str(e)}", "ERROR")
        return {"success": False, "message": str(e)}

@app.post("/api/instance/{name}/command")
async def send_instance_command(name: str, data: CommandRequest):
    """向实例发送命令"""
    try:
        # 这里应该实现向实例进程发送命令的逻辑
        # 例如：向进程的标准输入写入命令
        instance = version_controller.running_instances.get(name)
        
        if not instance or not instance.get("process"):
            raise HTTPException(status_code=404, detail="实例未运行")
        
        # 发送命令到进程
        process = instance["process"]
        process.stdin.write(f"{data.command}\n".encode())
        process.stdin.flush()
        
        return {"success": True}
    except Exception as e:
        XLogger.log(f"向实例发送命令失败: {str(e)}", "ERROR")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/api/logs/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # 保持连接活跃，客户端可以随时接收日志
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# 添加到日志回调
def log_callback(log_data, *args):
    """处理日志回调，兼容不同参数数量"""
    try:
        asyncio.create_task(manager.send_log(log_data))
    except Exception as e:
        print(f"日志回调处理异常: {e}")

# 设置回调
version_controller.set_log_callback(log_callback)
install_manager.set_install_callback(log_callback)

if __name__ == "__main__":
    import uvicorn
    XLogger.log("启动后端服务器")
    uvicorn.run(app, host="127.0.0.1", port=5000)

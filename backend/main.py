# -*- coding: utf-8 -*-
"""
X2 Launcher 后端服务
"""
import os
import sys
import traceback
from contextlib import asynccontextmanager

# 首先导入编码修复
try:
    from utils.encoding_fix import encoding_fixed
    if not encoding_fixed:
        print("警告：编码修复失败，可能会出现中文问题")
except Exception as e:
    print(f"编码修复失败: {e}")

# 确保当前目录在路径中，以便导入模块
current_dir = os.path.dirname(os.path.abspath(__file__))
if (current_dir not in sys.path):
    sys.path.append(current_dir)

# 尝试导入必要模块
try:
    import uvicorn
    from fastapi import FastAPI, WebSocket, HTTPException, Depends, BackgroundTasks
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
except ImportError as e:
    print(f"导入必要模块失败: {e}")
    print("请确保安装了所有依赖: pip install fastapi uvicorn pydantic websockets aiofiles")
    sys.exit(1)

# 这是新的推荐方式
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行的代码
    print("应用启动...")
    yield
    # 关闭时执行的代码
    print("应用关闭...")

# 创建FastAPI应用
app = FastAPI(
    title="X2 Launcher API",
    description="X2 Launcher 后端API服务",
    version="0.1.0",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源，生产环境应该限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 健康检查路由
@app.get("/api/health")
async def health_check():
    """健康检查API"""
    return {"status": "ok", "message": "服务正常运行"}

# 模拟状态API
@app.get("/api/status")
async def get_status():
    """获取系统状态"""
    return {
        "mongodb": {"status": "running", "info": "本地实例"},
        "napcat": {"status": "running", "info": "端口 8095"},
        "nonebot": {"status": "stopped", "info": ""},
        "maibot": {"status": "stopped", "info": ""}
    }

# 模拟实例列表API
@app.get("/api/instances")
async def get_instances():
    """获取实例列表"""
    return {
        "instances": [
            {
                "name": "maibot-latest",
                "path": "D:/maibot/latest",
                "installedAt": "2023-05-01 15:24:30",
                "status": "running",
                "services": {
                    "napcat": "running",
                    "nonebot": "stopped"
                }
            },
            {
                "name": "maibot-stable",
                "path": "D:/maibot/stable",
                "installedAt": "2023-04-15 10:33:22",
                "status": "stopped",
                "services": {
                    "napcat": "stopped",
                    "nonebot": "stopped"
                }
            }
        ]
    }

# 模拟日志API
@app.get("/api/logs/system")
async def get_system_logs():
    """获取系统日志"""
    return {
        "logs": [
            {"time": "2023-05-07 17:15:22", "level": "INFO", "message": "系统启动"},
            {"time": "2023-05-07 17:15:25", "level": "INFO", "message": "MongoDB 连接成功"},
            {"time": "2023-05-07 17:15:30", "level": "WARNING", "message": "NoneBot 适配器未启动"},
            {"time": "2023-05-07 17:16:45", "level": "ERROR", "message": "MaiBot 初始化失败: 配置文件损坏"}
        ]
    }

# WebSocket日志路由
@app.websocket("/api/logs/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        # 发送一条连接成功的消息
        await websocket.send_json({
            "time": "2023-05-07 17:30:00",
            "level": "INFO", 
            "message": "WebSocket连接已建立"
        })
        # 保持连接开启
        while True:
            await asyncio.sleep(60)
    except Exception:
        pass
    finally:
        try:
            await websocket.close()
        except:
            pass

# 如果是作为主程序运行
if __name__ == "__main__":
    print("后端服务启动中...")
    try:
        # 设置编码
        os.environ["PYTHONIOENCODING"] = "utf-8"
        
        # 添加缺少的asyncio导入
        import asyncio
        
        # 启动Uvicorn服务器
        uvicorn.run(
            app,  # 直接使用app实例
            host="127.0.0.1",
            port=5000,
            log_level="info",
            access_log=True
        )
    except Exception as e:
        print(f"启动服务器时发生错误: {e}")
        traceback.print_exc()
        sys.exit(1)

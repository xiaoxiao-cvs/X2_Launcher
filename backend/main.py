# -*- coding: utf-8 -*-
"""
X2 Launcher 后端主应用
"""
import os
import sys
import logging
import importlib
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("x2-launcher")
logger.info("正在启动X2 Launcher后端...")

# 创建FastAPI应用
app = FastAPI(
    title="X2 Launcher API",
    description="X2 Launcher后端API",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制为特定来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 设置API路由前缀
api_router = APIRouter(prefix="/api")

# 健康检查端点
@api_router.get("/health")
async def health_check():
    """健康检查API"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

# 引入其他路由
try:
    # 首先导入deploy路由
    from routes.deploy import router as deploy_router
    
    # 1. 先注册到根路由 - 处理不带/api前缀的请求 (如 /deploy)
    app.include_router(deploy_router)
    logger.info("已将部署路由注册到根路径")
    
    # 2. 再注册到API路由 - 处理带/api前缀的请求 (如 /api/deploy)
    api_router.include_router(deploy_router)
    logger.info("已将部署路由注册到API路径")
    
    # 加载其他API路由
    try:
        from routes.api import router as api_routes
        api_router.include_router(api_routes)
        logger.info("已加载通用API路由")
    except ImportError as e:
        logger.warning(f"加载通用API路由失败: {e}")
    
    try:
        from routes.websocket import router as ws_router
        api_router.include_router(ws_router)
        logger.info("已加载WebSocket路由")
    except ImportError as e:
        logger.warning(f"加载WebSocket路由失败: {e}")
        
except ImportError as e:
    logger.error(f"加载部署路由失败: {e}", exc_info=True)

# 包含API路由到主应用
app.include_router(api_router)

# 设置前端静态文件服务
try:
    frontend_path = Path(__file__).parent.parent / "frontend" / "dist"
    if frontend_path.exists():
        app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="static")
        logger.info(f"已挂载前端静态文件: {frontend_path}")
    else:
        logger.warning(f"前端目录不存在: {frontend_path}")
except Exception as e:
    logger.error(f"挂载前端静态文件失败: {e}", exc_info=True)

# 添加全局异常处理
@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc):
    path = request.url.path
    logger.warning(f"404请求: {path}")
    
    # 如果是API请求返回JSON
    if path.startswith("/api/"):
        return {"status": "error", "message": "API端点不存在", "path": path, "code": 404}
    
    # 否则返回前端应用(SPA路由)
    if frontend_path.exists():
        return StaticFiles(directory=str(frontend_path), html=True).get_response(
            "index.html", 
            scope=request.scope
        )
    
    # 前端不存在时返回简单消息
    return {"status": "error", "message": "资源不存在", "path": path}

if __name__ == "__main__":
    import uvicorn
    
    # 可以通过环境变量覆盖端口和主机
    port = int(os.environ.get("X2_PORT", 5000))
    host = os.environ.get("X2_HOST", "127.0.0.1")
    
    logger.info(f"启动服务器，监听地址: {host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=True)

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

# 首先确保编码正确
try:
    from utils.encoding_fix import fix_encoding
    fix_encoding()
except ImportError:
    print("警告: 无法导入编码修复模块，中文显示可能会有问题")

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
    # 加载其他API路由
    try:
        from api.api import router as api_routes
        api_router.include_router(api_routes, prefix="")
        logger.info("已加载通用API路由")
    except ImportError as e:
        logger.warning(f"加载通用API路由失败: {e}")
    
    try:
        from routes.websocket import router as ws_router
        api_router.include_router(ws_router, prefix="")
        logger.info("已加载WebSocket路由")
    except ImportError as e:
        logger.warning(f"加载WebSocket路由失败: {e}")
        
except ImportError as e: 
    logger.error(f"加载路由模块时发生意外错误: {e}", exc_info=True)

# 包含API路由到主应用
app.include_router(api_router)

# 设置前端静态文件服务
try:
    frontend_path = Path(__file__).parent.parent / "frontend" / "dist"
    if frontend_path.exists():
        app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="static")
        logger.info(f"已挂载前端静态文件: {frontend_path}")
    else:
        # 尝试创建基本的前端目录结构
        frontend_path.mkdir(parents=True, exist_ok=True)
        index_html = frontend_path / "index.html"
        if not index_html.exists():
            logger.warning(f"创建临时前端页面: {index_html}")
            with open(index_html, "w", encoding="utf-8") as f:
                f.write("""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>X² Launcher</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }
        h1 { color: #333; }
        .message { color: #666; margin: 20px; }
    </style>
</head>
<body>
    <h1>X² Launcher</h1>
    <div class="message">前端界面尚未构建，请先构建前端或访问API接口</div>
    <p>API状态检查: <a href="/api/health">点击这里</a></p>
</body>
</html>""")
        app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="static")
        logger.info(f"已创建并挂载临时前端页面")
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
    reload_enabled = os.environ.get("X2_RELOAD", "true").lower() == "true"
    
    # 检测是否在重载工作进程中
    is_reload_worker = os.environ.get("PYTHONPATH") and reload_enabled
    
    if not is_reload_worker:
        logger.info(f"启动服务器，监听地址: {host}:{port}")
    
    # 降低重载工作进程的日志级别，减少重复日志
    if is_reload_worker:
        logging.getLogger("x2-launcher").setLevel(logging.WARNING)
    
    uvicorn.run("main:app", host=host, port=port, reload=reload_enabled)

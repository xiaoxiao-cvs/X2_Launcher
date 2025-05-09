# -*- coding: utf-8 -*-
"""
X2 Launcher 后端服务 - 重构版
采用模块化设计，更好的错误处理和生命周期管理
"""
import os
import sys
import logging
import asyncio
import argparse
from contextlib import asynccontextmanager
from pathlib import Path

# 设置编码
os.environ["PYTHONIOENCODING"] = "utf-8"

# 确保当前目录在路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# 解析命令行参数
parser = argparse.ArgumentParser(description='X2 Launcher 后端服务')
parser.add_argument('--port', type=int, default=5000, help='服务端口号')
parser.add_argument('--host', type=str, default="127.0.0.1", help='服务主机地址')
args, unknown = parser.parse_known_args()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(current_dir, "launcher.log"), encoding="utf-8")
    ]
)
logger = logging.getLogger("x2-launcher")

try:
    # 导入必要模块
    import uvicorn
    from fastapi import FastAPI, Depends, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import JSONResponse
    
    # 导入API路由
    from routes.api import router as api_router
    from routes.deploy import router as deploy_router
    from routes.websocket import router as ws_router
    
    # 导入服务组件
    from services.system_info import SystemInfoService
    from services.instance_manager import InstanceManager
    
except ImportError as e:
    logger.critical(f"导入必要模块失败: {e}")
    logger.error("请确保安装了所有依赖: pip install fastapi uvicorn pydantic websockets aiofiles psutil")
    sys.exit(1)

# 应用生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    logger.info("X2 Launcher 服务启动中...")
    
    # 初始化服务组件
    app.state.instance_manager = InstanceManager()
    app.state.system_info = SystemInfoService()
    
    logger.info("服务组件初始化完成")
    
    try:
        yield
    finally:
        # 关闭时执行
        logger.info("X2 Launcher 服务正在关闭...")
        # 清理资源
        await app.state.instance_manager.shutdown()
        logger.info("服务已安全关闭")

# 全局异常处理
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"全局异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "内部服务器错误", "message": str(exc)}
    )

# 创建FastAPI应用
def create_app() -> FastAPI:
    app = FastAPI(
        title="X² Launcher API",
        description="MaiBot 启动器后端服务",
        version="0.2.0",
        lifespan=lifespan
    )
    
    # 配置全局异常处理
    app.add_exception_handler(Exception, global_exception_handler)
    
    # 添加CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境应该限制
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册API路由
    app.include_router(api_router, prefix="/api")
    app.include_router(deploy_router, prefix="/api")
    app.include_router(ws_router)
    
    # 挂载前端静态文件
    frontend_dir = Path(current_dir).parent / "frontend" / "dist"
    if frontend_dir.exists():
        app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="static")
        logger.info(f"前端静态文件已挂载: {frontend_dir}")
    else:
        logger.warning(f"前端静态文件目录不存在: {frontend_dir}")
    
    return app

# 实例化应用
app = create_app()

# 主入口
if __name__ == "__main__":
    try:
        print(f"✨ X² Launcher 后端服务启动中... (端口: {args.port})")
        
        # 检查必要文件夹
        os.makedirs(os.path.join(current_dir, "logs"), exist_ok=True)
        os.makedirs(os.path.join(current_dir, "temp"), exist_ok=True)
        
        # 启动服务器
        uvicorn.run(
            "main:app",
            host=args.host,
            port=args.port,
            log_level="info",
            reload=True  # 开发模式启用热重载
        )
    except KeyboardInterrupt:
        print("\n👋 服务已手动终止")
    except Exception as e:
        logger.critical(f"启动服务器失败: {e}", exc_info=True)
        print(f"\n❌ 启动失败: {e}")
        print("请运行 python diagnostic.py 进行诊断")
        sys.exit(1)

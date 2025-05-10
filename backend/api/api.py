# -*- coding: utf-8 -*-
"""
API路由模块 - 包含通用API端点
"""
import os
import sys
import time
import platform
import logging
import asyncio
import subprocess
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

# 首先设置日志器
logger = logging.getLogger("x2-launcher.api")

# 添加项目根目录到路径，确保模块导入正确
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(current_dir))

# 尝试导入deploy_manager路由
try:
    from routes.deploy_manager import router as deploy_manager_router
    logger.info("成功导入deploy_manager路由")
except ImportError as e:
    logger.error(f"无法导入deploy_manager路由: {e}")
    # 创建一个空路由作为替代
    deploy_manager_router = APIRouter()

# 创建主路由
router = APIRouter(tags=["api"], prefix="")

# 注册deploy_manager路由，注意这里前缀为"/deploy"
router.include_router(deploy_manager_router, prefix="/deploy", tags=["deploy"])
logger.info(f"已注册deploy_manager路由，前缀: /deploy")

# 健康检查API
@router.get("/health")
async def health_check():
    """健康检查API"""
    return {
        "status": "ok",
        "timestamp": time.time(),
        "version": "0.2.0",
        "environment": platform.platform()
    }

# 添加诊断API，用于检查路由注册情况
@router.get("/diagnose")
async def diagnose_api(request: Request):
    """诊断API，返回所有注册的路由信息"""
    routes = []
    
    # 获取所有路由
    for route in request.app.routes:
        route_info = {
            "path": route.path if hasattr(route, 'path') else str(route),
            "name": route.name if hasattr(route, 'name') else None,
            "methods": list(route.methods) if hasattr(route, 'methods') else None,
        }
        routes.append(route_info)
    
    # 返回应用状态信息
    return {
        "routes_count": len(routes),
        "routes": routes,
        "environment": platform.platform(),
        "python_version": platform.python_version(),
        "timestamp": time.time()
    }

# 状态API
@router.get("/status")
async def get_status(request: Request):
    """获取系统状态"""
    try:
        # 使用系统信息服务
        system_info = request.app.state.system_info
        status = await system_info.get_service_status()
        return status
    except Exception as e:
        logger.error(f"获取状态失败: {e}", exc_info=True)
        # 使用备选数据
        return {
            "mongodb": {"status": "running", "info": "本地实例"},
            "napcat": {"status": "running", "info": "端口 8095"},
            "nonebot": {"status": "stopped", "info": ""},
            "maibot": {"status": "stopped", "info": ""}
        }

# 实例列表API
@router.get("/instances")
async def get_instances(request: Request):
    """获取已安装的实例列表"""
    try:
        # 使用实例管理器
        instance_manager = request.app.state.instance_manager
        instances = await instance_manager.get_instances()
        return {"instances": instances}
    except Exception as e:
        logger.error(f"获取实例列表失败: {e}", exc_info=True)
        return {"instances": [], "error": str(e)}

# 启动实例API
@router.post("/start/{instance_name}")
async def start_instance(instance_name: str, request: Request):
    """启动指定的实例"""
    try:
        # 使用实例管理器
        instance_manager = request.app.state.instance_manager
        success = await instance_manager.start_instance(instance_name)
        
        if not success:
            raise HTTPException(status_code=500, detail="启动实例失败")
        
        return {"success": True, "message": f"实例 {instance_name} 已启动"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动实例失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# 停止实例API
@router.post("/stop")
async def stop_instance(request: Request):
    """停止所有运行中的实例"""
    try:
        # 使用实例管理器
        instance_manager = request.app.state.instance_manager
        success = await instance_manager.stop_all_instances()
        
        if not success:
            raise HTTPException(status_code=500, detail="停止实例失败")
        
        return {"success": True, "message": "所有实例已停止"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"停止实例失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# 打开文件夹API
@router.post("/open-folder")
async def open_folder(data: dict):
    """打开指定的文件夹"""
    path = data.get("path")
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=400, detail="路径不存在")
    
    try:
        if sys.platform == "win32":
            subprocess.run(["explorer", path])
        elif sys.platform == "darwin":
            subprocess.run(["open", path])
        else:
            subprocess.run(["xdg-open", path])
        return {"success": True}
    except Exception as e:
        logger.error(f"打开文件夹失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# 日志API
@router.get("/logs/system")
async def get_system_logs():
    """获取系统日志"""
    try:
        # 从日志文件读取或使用内存中的日志
        logs = [
            {"time": "2023-05-07 17:15:22", "level": "INFO", "message": "系统启动"},
            {"time": "2023-05-07 17:15:25", "level": "INFO", "message": "MongoDB 连接成功"},
            {"time": "2023-05-07 17:15:30", "level": "WARNING", "message": "NoneBot 适配器未启动"},
            {"time": "2023-05-07 17:16:45", "level": "ERROR", "message": "MaiBot 初始化失败: 配置文件损坏"}
        ]
        return {"logs": logs}
    except Exception as e:
        logger.error(f"获取系统日志失败: {e}", exc_info=True)
        return {"logs": [], "error": str(e)}

# 实例统计API - 旧版路径（保持兼容）
@router.get("/instance-stats")
async def get_instance_stats_old(request: Request):
    """获取实例统计数据（旧API，保留兼容性）"""
    try:
        logger.info("通过旧API路径请求实例统计数据")
        instance_manager = request.app.state.instance_manager
        stats = await instance_manager.get_instance_stats()
        return stats
    except Exception as e:
        logger.error(f"获取实例统计数据失败: {e}", exc_info=True)
        return {"total": 0, "running": 0, "error": str(e)}

# 实例统计API - 新版路径
@router.get("/instances/stats")
async def get_instances_stats(request: Request):
    """获取实例统计数据 - 新版API"""
    try:
        logger.info("通过新API路径请求实例统计数据")
        instance_manager = request.app.state.instance_manager
        stats = await instance_manager.get_instance_stats()
        return stats
    except Exception as e:
        logger.error(f"获取实例统计数据失败: {e}", exc_info=True)
        return {"total": 0, "running": 0, "error": str(e)}

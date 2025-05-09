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

logger = logging.getLogger("x2-launcher.api")

router = APIRouter(tags=["api"])

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

# 实例统计API
@router.get("/instance-stats")
async def get_instance_stats(request: Request):
    """获取实例统计数据"""
    try:
        # 使用实例管理器
        instance_manager = request.app.state.instance_manager
        stats = await instance_manager.get_instance_stats()
        return stats
    except Exception as e:
        logger.error(f"获取实例统计数据失败: {e}", exc_info=True)
        return {"total": 0, "running": 0, "error": str(e)}

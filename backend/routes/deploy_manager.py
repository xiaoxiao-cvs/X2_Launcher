# -*- coding: utf-8 -*-
"""
部署管理器路由模块
处理MaiBot实例的部署
"""
import os
import sys
import logging
from typing import Optional, Dict, Any

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel

# 设置日志
logger = logging.getLogger("x2-launcher.deploy")

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入下载器
try:
    from scripts.downloader import BotDownloader
except ImportError as e:
    logger.error(f"无法导入下载器模块: {e}")
    # 创建空的替代类，防止程序崩溃
    class BotDownloader:
        def __init__(self, *args, **kwargs): pass
        def download(self, *args, **kwargs): 
            return {"success": False, "message": "下载器模块未正确加载"}

# 创建路由
router = APIRouter()

class DeployRequest(BaseModel):
    instance_name: str
    version: Optional[str] = "latest"
    config: Optional[Dict[str, Any]] = None

@router.post("")
async def deploy_instance(request: DeployRequest = Body(...)):
    """部署一个新的MaiBot实例"""
    logger.info(f"收到部署请求: {request.instance_name}, 版本: {request.version}")
    
    try:
        # 初始化下载器
        downloader = BotDownloader(project_root)
        
        # 执行下载
        result = downloader.download(request.instance_name, request.version)
        
        if not result.get("success", False):
            logger.error(f"部署失败: {result.get('message', '未知错误')}")
            raise HTTPException(status_code=500, detail=result.get("message", "部署失败"))
        
        return {
            "success": True,
            "message": f"成功部署实例 {request.instance_name}",
            "data": result
        }
    except Exception as e:
        logger.exception(f"部署过程中发生错误: {e}")
        raise HTTPException(status_code=500, detail=f"部署过程中发生错误: {str(e)}")

@router.get("/versions")
async def get_available_versions():
    """获取可用的MaiBot版本"""
    # 这里可以从GitHub API获取实际版本列表
    # 简化示例实现
    return {
        "versions": [
            {"name": "latest", "description": "最新开发版"},
            {"name": "stable", "description": "最新稳定版"},
            {"name": "v1.0.0", "description": "正式版 1.0.0"},
            {"name": "v0.9.5", "description": "预发布版 0.9.5"}
        ]
    }

@router.get("/test")
async def test_endpoint():
    """测试端点，用于检查路由是否正常工作"""
    return {"status": "ok", "message": "deploy_manager 路由正常工作"}

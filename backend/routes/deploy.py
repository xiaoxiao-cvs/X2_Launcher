# -*- coding: utf-8 -*-
"""
部署相关API路由
"""
import os
import sys
import time
import logging
import asyncio
from typing import List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Depends

logger = logging.getLogger("x2-launcher.deploy")

# 使用空字符串作为标签，移除前缀，确保能匹配多种路径模式
router = APIRouter(tags=["deploy"])

# 全局变量，存储运行中的任务和日志
running_tasks = {}
task_logs = {}
install_status = {"napcat_installing": False, "nonebot_installing": False}

# 获取可用版本 - 注意不要使用以/开头的路径
@router.get("versions")
async def get_available_versions():
    """获取可用的MaiBot版本"""
    try:
        # 这里可以从GitHub API获取实际版本
        versions = ["latest", "main", "stable", "v0.6.3", "v0.6.2", "v0.6.1", "v0.6.0"]
        return {"versions": versions}
    except Exception as e:
        logger.error(f"获取版本失败: {e}", exc_info=True)
        # 使用备选版本
        return {
            "versions": ["latest", "main", "stable"],
            "fromCache": True,
            "isLocalFallback": True
        }

# 部署特定版本 - 支持/deploy/{version}路径
@router.post("deploy/{version}")
async def deploy_version(version: str, background_tasks: BackgroundTasks):
    """部署指定版本的MaiBot"""
    logger.info(f"收到部署请求: {version}")
    instance_name = f"maibot_{version}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # 后台执行部署任务
    background_tasks.add_task(download_bot, instance_name, version)
    
    return {
        "success": True,
        "message": f"正在部署 {version} 版本",
        "instance_name": instance_name,
        "timestamp": datetime.now().isoformat()
    }

# 通用部署端点 - 支持 /deploy 路径
@router.post("deploy")
async def deploy_version_api(data: dict, background_tasks: BackgroundTasks):
    """通过API路径接收部署请求
    
    Args:
        data: 包含version和instance_name的数据
    """
    version = data.get("version", "latest")
    instance_name = data.get("instance_name")
    
    logger.info(f"收到JSON部署请求: {version}, 实例名称: {instance_name}")
    
    if not instance_name:
        # 如果没有提供实例名称，则生成一个
        instance_name = f"maibot_{version}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # 后台执行部署任务
    background_tasks.add_task(download_bot, instance_name, version)
    
    return {
        "success": True,
        "message": f"正在部署 {version} 版本",
        "instance_name": instance_name,
        "timestamp": datetime.now().isoformat()
    }

# 获取部署状态
@router.get("deploy/status/{instance_name}")
async def get_deploy_status(instance_name: str):
    """获取部署状态"""
    if instance_name in running_tasks:
        return {
            "status": "running",
            "instance_name": instance_name,
            "logs": task_logs.get(instance_name, [])
        }
    
    # 检查是否有安装完成的记录
    install_path = os.path.join(os.path.expanduser("~"), "MaiM-with-u", instance_name)
    if os.path.exists(install_path):
        return {
            "status": "completed",
            "instance_name": instance_name,
            "install_path": install_path,
            "logs": task_logs.get(instance_name, [])
        }
    
    return {"status": "not_found", "instance_name": instance_name}

# 配置机器人 - 支持 /install/configure 路径
@router.post("install/configure")
async def configure_bot(config: Dict[str, Any], background_tasks: BackgroundTasks):
    """配置MaiBot"""
    logger.info(f"收到配置请求: {config.get('instance_name')}")
    instance_name = config.get("instance_name")
    if not instance_name:
        raise HTTPException(status_code=400, detail="缺少实例名称")
    
    # 检查实例是否存在
    install_path = os.path.join(os.path.expanduser("~"), "MaiM-with-u", instance_name)
    if not os.path.exists(install_path):
        raise HTTPException(status_code=404, detail=f"实例 {instance_name} 不存在")
    
    # 后台执行配置任务
    background_tasks.add_task(configure_bot_task, install_path, instance_name, config)
    
    return {
        "success": True,
        "message": f"正在配置实例 {instance_name}",
        "instance_name": instance_name
    }

# 获取安装状态 - 支持 /install-status 路径
@router.get("install-status")
async def get_install_status():
    """获取安装状态"""
    return install_status

# 实用函数 - 添加日志
async def add_log(instance_name: str, level: str, message: str):
    """添加日志"""
    if instance_name not in task_logs:
        task_logs[instance_name] = []
    
    log_entry = {
        "time": datetime.now().isoformat(),
        "level": level,
        "message": message
    }
    task_logs[instance_name].append(log_entry)
    
    # 限制日志条数
    if len(task_logs[instance_name]) > 1000:
        task_logs[instance_name] = task_logs[instance_name][-900:]

# 后台任务 - 下载机器人
async def download_bot(instance_name: str, version: str):
    """后台下载任务"""
    running_tasks[instance_name] = "downloading"
    
    try:
        await add_log(instance_name, "INFO", f"开始部署 {version} 版本")
        
        # 模拟下载过程
        await add_log(instance_name, "INFO", "克隆MaiBot和Adapter仓库...")
        await asyncio.sleep(2)  # 模拟延迟
        
        await add_log(instance_name, "SUCCESS", "仓库克隆成功")
        
        await add_log(instance_name, "INFO", "创建Python虚拟环境...")
        await asyncio.sleep(1)  # 模拟延迟
        
        await add_log(instance_name, "SUCCESS", "虚拟环境创建成功")
        
        await add_log(instance_name, "INFO", "安装MaiBot和Adapter依赖...")
        await asyncio.sleep(3)  # 模拟延迟
        
        await add_log(instance_name, "SUCCESS", "依赖安装成功")
        await add_log(instance_name, "INFO", "部署完成，可以继续配置")
        
    except Exception as e:
        logger.error(f"下载过程中出错: {e}", exc_info=True)
        await add_log(instance_name, "ERROR", f"部署过程出错: {str(e)}")
    finally:
        running_tasks.pop(instance_name, None)

# 后台任务 - 配置机器人
async def configure_bot_task(install_path: str, instance_name: str, config: Dict[str, Any]):
    """后台配置任务"""
    try:
        # 更新安装状态
        install_status["napcat_installing"] = config.get("install_napcat", False)
        install_status["nonebot_installing"] = config.get("install_nonebot", False)
        
        # 模拟配置过程
        await add_log(instance_name, "INFO", f"开始配置实例 {instance_name}")
        
        await add_log(instance_name, "INFO", "配置MaiBot...")
        await asyncio.sleep(1)  # 模拟延迟
        
        maibot_port = config.get("ports", {}).get("maibot", 8000)
        await add_log(instance_name, "SUCCESS", f"MaiBot配置成功，端口: {maibot_port}")
        
        # 配置Adapter
        if config.get("install_napcat") or config.get("install_nonebot"):
            await add_log(instance_name, "INFO", "配置MaiBot-Napcat-Adapter...")
            await asyncio.sleep(1)  # 模拟延迟
            
            qq_number = config.get("qq_number", "")
            napcat_port = config.get("ports", {}).get("napcat", 8095)
            nonebot_port = config.get("ports", {}).get("nonebot", 18002)
            
            await add_log(instance_name, "SUCCESS", 
                         f"Adapter配置成功，QQ: {qq_number}，NapCat端口: {napcat_port}，NoneBot端口: {nonebot_port}")
        
        await add_log(instance_name, "INFO", "已创建NapCat配置指南")
        
        await add_log(instance_name, "SUCCESS", "启动脚本创建成功")
        
        # 运行安装脚本（如果需要）
        if config.get("run_install_script", False):
            await add_log(instance_name, "INFO", "正在执行安装脚本...")
            await asyncio.sleep(2)  # 模拟延迟
            await add_log(instance_name, "SUCCESS", "安装脚本执行完成")
        
        # 安装适配器（如果需要）
        if config.get("install_adapter", False):
            await add_log(instance_name, "INFO", "正在安装NoneBot适配器...")
            await asyncio.sleep(2)  # 模拟延迟
            await add_log(instance_name, "SUCCESS", "NoneBot适配器安装完成")
        
        await add_log(instance_name, "SUCCESS", "配置过程全部完成，MaiBot实例已准备就绪")
        
    except Exception as e:
        logger.error(f"配置过程中出错: {e}", exc_info=True)
        await add_log(instance_name, "ERROR", f"配置过程出错: {str(e)}")
    finally:
        # 更新安装状态
        install_status["napcat_installing"] = False
        install_status["nonebot_installing"] = False

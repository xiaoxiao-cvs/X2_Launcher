# -*- coding: utf-8 -*-
"""
部署相关API路由
"""
import os
import sys
import time
import logging
import asyncio
import subprocess
from typing import List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Depends, Body

# 导入自定义模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.downloader import BotDownloader
from scripts.configurator import BotConfigurator

logger = logging.getLogger("x2-launcher.deploy")

# 使用标准路由配置，不设置前缀，由主应用处理
router = APIRouter(tags=["deploy"])

# 全局变量，存储运行中的任务和日志
running_tasks = {}
task_logs = {}
install_status = {"napcat_installing": False, "nonebot_installing": False}

# 获取可用版本
@router.get("/versions")
async def get_available_versions():
    """获取可用的MaiBot版本"""
    logger.info("收到获取版本请求")
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

# 部署特定版本
@router.post("/deploy/{version}")
async def deploy_version(version: str, background_tasks: BackgroundTasks, instance_name: str = None):
    """部署指定版本的MaiBot"""
    logger.info(f"收到部署请求 (URL路径参数): 版本={version}, 实例名称={instance_name}")
    
    # 如果没有提供实例名称，则生成一个
    if not instance_name:
        instance_name = f"MaiBot-{version}"
    
    # 后台执行部署任务
    background_tasks.add_task(download_bot_base, instance_name, version)
    
    return {
        "success": True,
        "message": f"正在部署 {version} 版本",
        "instance_name": instance_name,
        "timestamp": datetime.now().isoformat()
    }

# 通用部署端点 (基础下载和初始设置)
@router.post("/deploy") # 改为 /deploy 以匹配前端API调用
async def deploy_version_api(data: dict = Body(...), background_tasks: BackgroundTasks = None):
    """通过API路径接收部署请求 (基础下载)
    
    Args:
        data: 包含version和instance_name的数据
        background_tasks: 后台任务
    """
    version = data.get("version", "latest")
    instance_name = data.get("instance_name")
    
    logger.info(f"收到基础部署请求: 版本={version}, 实例名称={instance_name}")
    print(f"【部署API】收到基础部署请求: 版本={version}, 实例名称={instance_name}")
    
    if not instance_name:
        current_time = datetime.now().strftime("%m%d%H%M")
        instance_name = f"MaiBot-{version}-{current_time}"
        logger.info(f"自动生成实例名称: {instance_name}")
        print(f"【部署API】自动生成实例名称: {instance_name}")
    
    instance_path = os.path.join(os.getcwd(), "MaiM-with-u", instance_name)
    if os.path.exists(instance_path):
        logger.warning(f"实例路径已存在，可能被覆盖: {instance_path}")
        print(f"【部署API】警告: 实例路径已存在，可能被覆盖: {instance_path}")
        # 允许覆盖，downloader.py 中的 _clean_instance 会处理清理
    
    # 后台执行基础下载和设置任务
    if background_tasks:
        background_tasks.add_task(download_bot_base, instance_name, version) # 改为调用 download_bot_base
    else:
        asyncio.create_task(download_bot_base(instance_name, version))
    
    return {
        "success": True,
        "message": f"基础部署任务已启动: {version} 版本, 实例 {instance_name}",
        "instance_name": instance_name,
        "timestamp": datetime.now().isoformat()
    }

# 获取部署状态
@router.get("/deploy/status/{instance_name}")
async def get_deploy_status(instance_name: str):
    """获取部署状态"""
    logger.info(f"查询部署状态: {instance_name}")
    
    if instance_name in running_tasks:
        return {
            "status": "running",
            "instance_name": instance_name,
            "logs": task_logs.get(instance_name, [])
        }
    
    # 检查是否有安装完成的记录
    install_path = os.path.join(os.getcwd(), "MaiM-with-u", instance_name)
    if os.path.exists(install_path):
        return {
            "status": "completed",
            "instance_name": instance_name,
            "install_path": install_path,
            "logs": task_logs.get(instance_name, [])
        }
    
    return {"status": "not_found", "instance_name": instance_name}

# 配置机器人 (详细配置)
@router.post("/install/configure") # 路径保持不变
async def configure_bot_endpoint(config: Dict[str, Any], background_tasks: BackgroundTasks): # Renamed function for clarity
    """配置MaiBot实例的详细设置"""
    instance_name = config.get("instance_name")
    logger.info(f"收到详细配置请求: 实例 {instance_name}, 配置: {config}")
    print(f"【配置API】收到详细配置请求: 实例 {instance_name}")
    
    if not instance_name:
        logger.error("配置请求缺少实例名称")
        raise HTTPException(status_code=400, detail="配置请求缺少实例名称")
    
    install_path = os.path.join(os.getcwd(), "MaiM-with-u", instance_name)
    if not os.path.exists(install_path):
        logger.error(f"实例基础目录不存在，无法配置: {install_path}")
        print(f"【配置API】错误: 实例基础目录不存在: {install_path}")
        # 理论上此时基础部署应该已创建目录，如果不存在则说明第一步有问题
        raise HTTPException(status_code=404, detail=f"实例 {instance_name} 基础目录不存在，请先完成基础部署")
    
    # 后台执行详细配置任务
    background_tasks.add_task(configure_bot_detailed, install_path, instance_name, config) # 改为调用 configure_bot_detailed
    
    return {
        "success": True,
        "message": f"详细配置任务已启动: 实例 {instance_name}",
        "instance_name": instance_name
    }

# 获取安装状态
@router.get("/install-status")
async def get_install_status():
    """获取安装状态"""
    logger.info("查询安装状态")
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
    
    # 打印日志到控制台
    logger.info(f"[{instance_name}][{level}] {message}")
    print(f"【日志】[{instance_name}][{level}] {message}")

# 日志收集类，用于捕获子进程日志
class LogCollector:
    def __init__(self, instance_name):
        self.instance_name = instance_name
        self.buffer = []
    
    async def process_line(self, line):
        if line.strip():
            # 确定日志级别
            level = "INFO"
            if "错误" in line.lower() or "error" in line.lower():
                level = "ERROR"
            elif "警告" in line.lower() or "warning" in line.lower():
                level = "WARNING"
            elif "成功" in line.lower() or "success" in line.lower():
                level = "SUCCESS"
            
            # 添加到日志
            await add_log(self.instance_name, level, line.strip())
            # 打印到控制台
            print(f"【日志收集】[{self.instance_name}] {line.strip()}")
    
    def write(self, data):
        for line in data.splitlines():
            loop = asyncio.get_event_loop()
            loop.create_task(self.process_line(line))
    
    def flush(self):
        pass

# 后台任务 - 下载机器人 (基础)
async def download_bot_base(instance_name: str, version: str):
    """后台下载和基础设置任务"""
    running_tasks[instance_name] = "downloading_base" # 更新任务状态标记
    
    try:
        await add_log(instance_name, "INFO", f"开始基础部署 MaiBot {version} 到实例 {instance_name}")
        print(f"【基础下载任务】启动: MaiBot {version}, 实例 {instance_name}")
        
        downloader = BotDownloader()
        result = downloader.download(instance_name, version) # download 方法应只做基础下载和依赖安装
        
        if result.get("success"):
            install_path = result.get("base_dir", os.path.join(os.getcwd(), "MaiM-with-u", instance_name))
            if not os.path.exists(install_path): # Double check
                await add_log(instance_name, "ERROR", f"基础部署后实例目录 {install_path} 仍不存在")
                running_tasks.pop(instance_name, None)
                return

            await add_log(instance_name, "SUCCESS", "基础版本下载和依赖安装完成。")
            print(f"【基础下载任务】{instance_name} 基础下载完成")
            # 基础下载完成后，不清除 running_tasks，等待配置步骤或超时
            # running_tasks.pop(instance_name, None) # 不在此处移除，配置步骤会更新或最终由轮询超时处理
            running_tasks[instance_name] = "base_downloaded" # 更新状态
        else:
            error_message = result.get("message", "基础下载未知错误")
            await add_log(instance_name, "ERROR", f"基础下载失败: {error_message}")
            print(f"【基础下载任务】{instance_name} 基础下载失败: {error_message}")
            running_tasks.pop(instance_name, None) # 失败则移除
            
    except Exception as e:
        error_message = f"基础下载过程中发生异常: {str(e)}"
        await add_log(instance_name, "ERROR", error_message)
        logger.error(error_message, exc_info=True)
        print(f"【基础下载任务】{instance_name} 异常: {str(e)}")
        running_tasks.pop(instance_name, None)

# 后台任务 - 配置机器人 (详细)
async def configure_bot_detailed(install_path: str, instance_name: str, config: Dict[str, Any]):
    """后台详细配置任务"""
    running_tasks[instance_name] = "configuring_detailed" # 更新任务状态标记
    original_stdout = sys.stdout
    log_collector = LogCollector(instance_name)

    try:
        # 更新前端轮询所需的状态
        install_status["napcat_installing"] = config.get("install_napcat", False)
        # 假设 install_adapter 对应的是 nonebot (适配器) 的安装过程
        install_status["nonebot_installing"] = config.get("install_adapter", False)

        await add_log(instance_name, "INFO", f"开始详细配置实例 {instance_name}")
        print(f"【详细配置任务】启动: 实例 {instance_name}")
        
        # 重定向标准输出到日志收集器
        sys.stdout = log_collector

        configurator = BotConfigurator(install_path, instance_name)
        
        # 从前端传递过来的参数中提取所需配置
        # config 字典中应包含: qq_number, install_napcat, install_adapter, ports (内含 maibot, adapter, napcat)
        # model_type 等其他参数也可以包含在 config 中传递
        
        config_result = configurator.configure(config) # configure 方法应能处理这些参数
        
        sys.stdout = original_stdout # 恢复标准输出
        
        if config_result["success"]:
            await add_log(instance_name, "SUCCESS", f"实例 {instance_name} 详细配置成功。")
            await add_log(instance_name, "INFO", "所有安装和配置步骤已完成。")
            print(f"【详细配置任务】{instance_name} 配置成功")
        else:
            await add_log(instance_name, "ERROR", f"详细配置失败: {config_result['message']}")
            print(f"【详细配置任务】{instance_name} 配置失败: {config_result['message']}")
        
    except Exception as e:
        if sys.stdout != original_stdout: #确保恢复
            sys.stdout = original_stdout
        logger.error(f"详细配置过程中出错: {e}", exc_info=True)
        print(f"【详细配置任务】{instance_name} 异常: {str(e)}")
        await add_log(instance_name, "ERROR", f"详细配置过程出错: {str(e)}")
    finally:
        install_status["napcat_installing"] = False
        install_status["nonebot_installing"] = False
        running_tasks.pop(instance_name, None) # 任务完成或失败后移除
        print(f"【详细配置任务】{instance_name} 任务结束")

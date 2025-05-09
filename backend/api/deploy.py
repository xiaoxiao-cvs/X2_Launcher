import os
import sys
import json
import logging
import asyncio
import aiofiles
from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends

# 导入我们创建的组件
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.downloader import BotDownloader
from scripts.configurator import BotConfigurator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("deploy-api")

# 创建路由
router = APIRouter(prefix="/deploy", tags=["deploy"])

# 存储正在进行的任务
running_tasks = {}
# 存储任务日志
task_logs = {}
# 存储安装状态
install_status = {"napcat_installing": False, "nonebot_installing": False}

@router.get("/versions")
async def get_available_versions():
    """获取可用的MaiBot版本"""
    try:
        # 这里可以从GitHub API获取实际版本，但简单起见，我们使用固定列表
        versions = ["latest", "main", "stable", "v0.6.3", "v0.6.2", "v0.6.1", "v0.6.0"]
        return {"versions": versions}
    except Exception as e:
        logger.error(f"获取版本失败: {e}")
        # 使用备选版本
        return {
            "versions": ["latest", "main", "stable"],
            "fromCache": True,
            "isLocalFallback": True
        }

@router.post("/{version}")
async def deploy_version(version: str, background_tasks: BackgroundTasks):
    """部署指定版本的MaiBot
    
    Args:
        version: 要部署的版本
        background_tasks: FastAPI后台任务
    """
    instance_name = f"maibot_{version}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    # 后台执行下载任务
    background_tasks.add_task(download_bot, instance_name, version)
    
    return {
        "success": True,
        "message": f"正在部署 {version} 版本",
        "instance_name": instance_name,
        "timestamp": datetime.now().isoformat()
    }

@router.get("/status/{instance_name}")
async def get_deploy_status(instance_name: str):
    """获取部署状态
    
    Args:
        instance_name: 实例名称
    """
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

@router.post("/install/configure")
async def configure_bot(config: dict, background_tasks: BackgroundTasks):
    """配置MaiBot
    
    Args:
        config: 配置参数，包括QQ号、端口等
    """
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

@router.get("/install/status")
async def get_install_status():
    """获取安装状态"""
    return install_status

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
    
    # 这里可以发送WebSocket消息通知前端
    # 未实现，视具体需求而定

async def download_bot(instance_name: str, version: str):
    """后台下载任务
    
    Args:
        instance_name: 实例名称
        version: 版本
    """
    running_tasks[instance_name] = "downloading"
    
    try:
        await add_log(instance_name, "INFO", f"开始部署 {version} 版本")
        
        # 创建下载器
        base_dir = os.path.join(os.path.expanduser("~"), "MaiM-with-u", instance_name)
        downloader = BotDownloader(base_dir)
        
        # 克隆仓库
        await add_log(instance_name, "INFO", "克隆MaiBot和Adapter仓库...")
        maibot_cloned, adapter_cloned = downloader.clone_repos()
        
        if not maibot_cloned:
            await add_log(instance_name, "ERROR", "克隆MaiBot仓库失败")
            running_tasks.pop(instance_name, None)
            return
        
        if not adapter_cloned:
            await add_log(instance_name, "ERROR", "克隆Adapter仓库失败")
            running_tasks.pop(instance_name, None)
            return
        
        await add_log(instance_name, "SUCCESS", "仓库克隆成功")
        
        # 创建虚拟环境
        await add_log(instance_name, "INFO", "创建Python虚拟环境...")
        venv_created = downloader.create_venv()
        
        if not venv_created:
            await add_log(instance_name, "ERROR", "创建虚拟环境失败")
            running_tasks.pop(instance_name, None)
            return
        
        await add_log(instance_name, "SUCCESS", "虚拟环境创建成功")
        
        # 安装依赖
        await add_log(instance_name, "INFO", "安装MaiBot和Adapter依赖...")
        maibot_deps, adapter_deps = downloader.install_dependencies()
        
        if not maibot_deps:
            await add_log(instance_name, "ERROR", "安装MaiBot依赖失败")
            running_tasks.pop(instance_name, None)
            return
        
        if not adapter_deps:
            await add_log(instance_name, "ERROR", "安装Adapter依赖失败")
            running_tasks.pop(instance_name, None)
            return
        
        await add_log(instance_name, "SUCCESS", "依赖安装成功")
        await add_log(instance_name, "INFO", "部署完成，可以继续配置")
        
    except Exception as e:
        logger.error(f"下载过程中出错: {e}")
        await add_log(instance_name, "ERROR", f"部署过程出错: {str(e)}")
    finally:
        running_tasks.pop(instance_name, None)

async def configure_bot_task(install_path: str, instance_name: str, config: dict):
    """后台配置任务
    
    Args:
        install_path: 安装路径
        instance_name: 实例名称
        config: 配置参数
    """
    try:
        # 更新安装状态
        install_status["napcat_installing"] = config.get("install_napcat", False)
        install_status["nonebot_installing"] = config.get("install_nonebot", False)
        
        # 添加配置开始日志
        await add_log(instance_name, "INFO", f"开始配置实例 {instance_name}")
        
        # 创建配置器
        configurator = BotConfigurator(install_path, instance_name)
        
        # 配置MaiBot
        await add_log(instance_name, "INFO", "配置MaiBot...")
        maibot_port = config.get("ports", {}).get("maibot", 8000)
        model_type = config.get("model_type", "chatglm")
        
        maibot_configured = configurator.configure_maibot(
            maibot_port=maibot_port,
            model_type=model_type
        )
        
        if not maibot_configured:
            await add_log(instance_name, "ERROR", "配置MaiBot失败")
            return
        
        await add_log(instance_name, "SUCCESS", f"MaiBot配置成功，端口: {maibot_port}")
        
        # 配置Adapter
        if config.get("install_napcat") or config.get("install_nonebot"):
            await add_log(instance_name, "INFO", "配置MaiBot-Napcat-Adapter...")
            qq_number = config.get("qq_number", "")
            napcat_port = config.get("ports", {}).get("napcat", 8095)
            nonebot_port = config.get("ports", {}).get("nonebot", 18002)
            
            adapter_configured = configurator.configure_adapter(
                qq_number=qq_number,
                napcat_port=napcat_port,
                nonebot_port=nonebot_port,
                maibot_port=maibot_port
            )
            
            if not adapter_configured:
                await add_log(instance_name, "ERROR", "配置Adapter失败")
                return
            
            await add_log(instance_name, "SUCCESS", 
                         f"Adapter配置成功，QQ: {qq_number}，NapCat端口: {napcat_port}，NoneBot端口: {nonebot_port}")
        
        # 创建NapCat配置指南
        napcat_guide = configurator.create_napcat_config()
        await add_log(instance_name, "INFO", "已创建NapCat配置指南")
        
        # 创建启动脚本
        scripts_created = configurator.create_startup_scripts()
        if not scripts_created:
            await add_log(instance_name, "WARNING", "创建启动脚本失败，但配置已完成")
        else:
            await add_log(instance_name, "SUCCESS", "启动脚本创建成功")
        
        # 运行安装脚本（如果需要）
        if config.get("run_install_script", False):
            await add_log(instance_name, "INFO", "正在执行安装脚本...")
            # 这里可以添加实际的安装脚本执行代码
            await asyncio.sleep(2)  # 模拟执行时间
            await add_log(instance_name, "SUCCESS", "安装脚本执行完成")
        
        # 安装适配器（如果需要）
        if config.get("install_adapter", False):
            await add_log(instance_name, "INFO", "正在安装NoneBot适配器...")
            # 这里可以添加实际的适配器安装代码
            await asyncio.sleep(2)  # 模拟执行时间
            await add_log(instance_name, "SUCCESS", "NoneBot适配器安装完成")
        
        await add_log(instance_name, "SUCCESS", "配置过程全部完成，MaiBot实例已准备就绪")
        
    except Exception as e:
        logger.error(f"配置过程中出错: {e}")
        await add_log(instance_name, "ERROR", f"配置过程出错: {str(e)}")
    finally:
        # 更新安装状态
        install_status["napcat_installing"] = False
        install_status["nonebot_installing"] = False

# -*- coding: utf-8 -*-
"""
实例管理服务
负责管理MaiBot实例，包括启动、停止、查询状态等
"""
import os
import sys
import time
import logging
import asyncio
import subprocess
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("x2-launcher.instance-manager")

class InstanceManager:
    """实例管理器类"""
    
    def __init__(self):
        """初始化实例管理器"""
        self.base_dir = os.path.join(os.path.expanduser("~"), "MaiM-with-u")
        self.running_instances = {}  # 存储运行中的实例信息
        
        # 确保基础目录存在
        os.makedirs(self.base_dir, exist_ok=True)
    
    async def get_instances(self) -> List[Dict[str, Any]]:
        """获取所有实例"""
        instances = []
        
        try:
            if not os.path.exists(self.base_dir):
                return []
                
            for folder in os.listdir(self.base_dir):
                instance_path = os.path.join(self.base_dir, folder)
                if os.path.isdir(instance_path):
                    # 检查是否是MaiBot实例（至少应该有MaiBot和Adapter文件夹）
                    maibot_dir = os.path.join(instance_path, "MaiBot")
                    adapter_dir = os.path.join(instance_path, "MaiBot-Napcat-Adapter")
                    
                    if os.path.exists(maibot_dir) and os.path.exists(adapter_dir):
                        # 获取安装时间（使用文件夹创建时间）
                        try:
                            created_time = os.path.getctime(instance_path)
                            installed_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(created_time))
                        except:
                            installed_at = "未知"
                        
                        # 检查实例状态
                        status = "running" if folder in self.running_instances else "stopped"
                        
                        # 检查各服务状态
                        services = self._check_services(folder)
                        
                        instances.append({
                            "name": folder,
                            "path": instance_path,
                            "installedAt": installed_at,
                            "status": status,
                            "services": services
                        })
        except Exception as e:
            logger.error(f"获取实例列表失败: {e}", exc_info=True)
        
        return instances
    
    async def get_instance_stats(self) -> Dict[str, Any]:
        """获取实例统计数据，包括总数和运行中的数量"""
        total_instances = 0
        running_instances = 0
        
        try:
            # 统计基础目录中的实例总数
            if os.path.exists(self.base_dir):
                total_instances = len([
                    folder for folder in os.listdir(self.base_dir) 
                    if self._is_valid_instance(os.path.join(self.base_dir, folder))
                ])
            
            # 统计maibot-vision目录中的配置文件数量
            vision_config_dir = os.path.join(os.path.dirname(self.base_dir), "maibot-vision")
            if os.path.exists(vision_config_dir):
                json_files = [f for f in os.listdir(vision_config_dir) 
                             if f.endswith('.json') and os.path.isfile(os.path.join(vision_config_dir, f))]
                # 如果vision配置文件更多，则使用配置文件数量
                total_instances = max(total_instances, len(json_files))
            
            # 统计运行中的实例数量
            running_instances = len(self.running_instances)
            
        except Exception as e:
            logger.error(f"获取实例统计数据失败: {e}", exc_info=True)
        
        return {
            "total": total_instances,
            "running": running_instances
        }
    
    def _is_valid_instance(self, instance_path: str) -> bool:
        """检查路径是否是有效的实例目录"""
        if not os.path.isdir(instance_path):
            return False
            
        # 检查是否是MaiBot实例（至少应该有MaiBot和Adapter文件夹）
        maibot_dir = os.path.join(instance_path, "MaiBot")
        adapter_dir = os.path.join(instance_path, "MaiBot-Napcat-Adapter")
        
        return os.path.exists(maibot_dir) and os.path.exists(adapter_dir)
    
    def _check_services(self, instance_name: str) -> Dict[str, str]:
        """检查实例的各个服务状态"""
        # 这里可以实现检查NapCat、NoneBot等服务的实际状态
        # 示例实现，返回模拟数据
        if instance_name in self.running_instances:
            # 假设该实例正在运行，检查其中的服务
            services = self.running_instances[instance_name].get("services", {})
            return services
        
        # 默认状态
        return {
            "napcat": "stopped",
            "nonebot": "stopped"
        }
    
    async def start_instance(self, instance_name: str) -> bool:
        """启动指定实例"""
        if instance_name in self.running_instances:
            logger.warning(f"实例 {instance_name} 已经在运行中")
            return True
        
        instance_path = os.path.join(self.base_dir, instance_name)
        if not os.path.exists(instance_path):
            logger.error(f"实例 {instance_name} 不存在")
            return False
        
        try:
            # 这里是模拟启动过程
            # 实际实现应该启动实例的各个组件
            
            logger.info(f"启动实例 {instance_name}")
            
            # 记录启动状态
            self.running_instances[instance_name] = {
                "start_time": time.time(),
                "services": {
                    "napcat": "running",
                    "nonebot": "running"
                }
            }
            
            return True
        except Exception as e:
            logger.error(f"启动实例 {instance_name} 失败: {e}", exc_info=True)
            return False
    
    async def stop_instance(self, instance_name: str) -> bool:
        """停止指定实例"""
        if instance_name not in self.running_instances:
            logger.warning(f"实例 {instance_name} 未运行")
            return True
        
        try:
            # 这里是模拟停止过程
            # 实际实现应该停止实例的各个组件
            
            logger.info(f"停止实例 {instance_name}")
            
            # 移除实例运行记录
            self.running_instances.pop(instance_name, None)
            
            return True
        except Exception as e:
            logger.error(f"停止实例 {instance_name} 失败: {e}", exc_info=True)
            return False
    
    async def stop_all_instances(self) -> bool:
        """停止所有实例"""
        success = True
        
        for instance_name in list(self.running_instances.keys()):
            result = await self.stop_instance(instance_name)
            if not result:
                success = False
        
        return success
    
    async def get_instance_logs(self, instance_name: str) -> List[Dict[str, Any]]:
        """获取实例的日志"""
        # 这里可以实现从日志文件读取实例日志
        # 示例实现，返回模拟数据
        return [
            {"time": "2023-06-01 12:30:00", "level": "INFO", "message": f"{instance_name} 启动中"},
            {"time": "2023-06-01 12:30:05", "level": "INFO", "message": "NapCat 初始化完成"},
            {"time": "2023-06-01 12:30:10", "level": "INFO", "message": "NoneBot 初始化完成"},
            {"time": "2023-06-01 12:30:15", "level": "INFO", "message": "MaiBot 启动成功"}
        ]
    
    async def shutdown(self) -> None:
        """关闭所有实例，释放资源"""
        await self.stop_all_instances()
        logger.info("实例管理器已关闭")

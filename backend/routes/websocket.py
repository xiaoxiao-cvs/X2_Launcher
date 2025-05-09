# -*- coding: utf-8 -*-
"""
WebSocket路由模块
"""
import json
import logging
import asyncio
from typing import List, Dict, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger("x2-launcher.websocket")

router = APIRouter(tags=["websocket"])

# WebSocket连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_info: Dict[WebSocket, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket):
        """连接WebSocket"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_info[websocket] = {
            "subscribed_logs": [],  # 订阅的日志类型
            "instance_name": None,  # 关联的实例名称
        }
        logger.debug(f"WebSocket连接建立，当前连接数: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """断开WebSocket连接"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        if websocket in self.connection_info:
            del self.connection_info[websocket]
            
        logger.debug(f"WebSocket连接断开，当前连接数: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """发送个人消息"""
        if websocket in self.active_connections:
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"发送WebSocket消息失败: {e}")
                await self.disconnect(websocket)

    async def broadcast(self, message: str):
        """广播消息给所有连接"""
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"广播消息失败: {e}")
                await self.disconnect(connection)
    
    async def broadcast_log(self, log_data: Dict[str, Any]):
        """广播日志数据"""
        message = json.dumps(log_data)
        
        for connection in self.active_connections:
            info = self.connection_info.get(connection, {})
            subscribed_logs = info.get("subscribed_logs", [])
            instance_name = info.get("instance_name")
            
            # 如果连接订阅了此日志类型或关联了此实例
            if not subscribed_logs or log_data.get("source") in subscribed_logs or log_data.get("instance") == instance_name:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error(f"广播日志失败: {e}")
                    await self.disconnect(connection)

# 创建连接管理器实例
manager = ConnectionManager()

# WebSocket路由
@router.websocket("/api/logs/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket日志接入点"""
    await manager.connect(websocket)
    try:
        while True:
            # 接收客户端消息
            text_data = await websocket.receive_text()
            
            try:
                data = json.loads(text_data)
                
                # 处理ping命令
                if data.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong", "timestamp": data.get("timestamp")}))
                
                # 处理订阅命令
                elif data.get("type") == "subscribe":
                    log_types = data.get("log_types", [])
                    if websocket in manager.connection_info:
                        manager.connection_info[websocket]["subscribed_logs"] = log_types
                    await websocket.send_text(json.dumps({
                        "type": "subscribe_success",
                        "subscribed": log_types
                    }))
                
                # 处理设置实例命令
                elif data.get("type") == "set_instance":
                    instance_name = data.get("instance_name")
                    if websocket in manager.connection_info:
                        manager.connection_info[websocket]["instance_name"] = instance_name
                    await websocket.send_text(json.dumps({
                        "type": "set_instance_success",
                        "instance_name": instance_name
                    }))
                
                # 其他命令
                else:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "未知命令"
                    }))
                    
            except json.JSONDecodeError:
                logger.warning(f"接收到无效的JSON数据: {text_data}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "无效的JSON格式"
                }))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket处理出错: {e}", exc_info=True)
        manager.disconnect(websocket)

# 模拟日志发送示例
async def send_test_logs():
    """定期发送测试日志"""
    while True:
        await manager.broadcast_log({
            "time": "2023-06-01 12:30:45",
            "level": "INFO",
            "message": "测试日志消息",
            "source": "system"
        })
        await asyncio.sleep(5)  # 每5秒发送一条

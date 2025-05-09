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

# 存储活动的WebSocket连接
active_connections: List[WebSocket] = []

@router.websocket("/api/logs/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket日志端点"""
    await websocket.accept()
    active_connections.append(websocket)
    logger.info(f"WebSocket连接已建立，当前连接数: {len(active_connections)}")
    
    try:
        # 发送连接成功消息
        await websocket.send_json({
            "time": "now",
            "level": "INFO",
            "message": "WebSocket连接已建立",
            "source": "system"
        })
        
        # 等待消息
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            
            try:
                msg = json.loads(data)
                logger.info(f"收到WebSocket消息: {msg}")
                # 处理消息
                # ...
            except json.JSONDecodeError:
                logger.warning(f"收到无效的WebSocket消息: {data}")
    
    except WebSocketDisconnect:
        # 客户端断开连接
        logger.info("WebSocket连接已关闭")
    except Exception as e:
        # 其他错误
        logger.error(f"WebSocket错误: {e}", exc_info=True)
    finally:
        # 移除连接
        if websocket in active_connections:
            active_connections.remove(websocket)
        logger.info(f"WebSocket连接已关闭，剩余连接数: {len(active_connections)}")

# 广播消息的函数
async def broadcast_log(message: Dict[str, Any]):
    """向所有连接的客户端广播日志消息"""
    disconnected = []
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except Exception:
            disconnected.append(connection)
    
    # 移除已断开的连接
    for conn in disconnected:
        if conn in active_connections:
            active_connections.remove(conn)

# 模拟日志发送示例
async def send_test_logs():
    """定期发送测试日志"""
    while True:
        await broadcast_log({
            "time": "2023-06-01 12:30:45",
            "level": "INFO",
            "message": "测试日志消息",
            "source": "system"
        })
        await asyncio.sleep(5)  # 每5秒发送一条

import logging
import sys
import time
from typing import Optional, Callable, List, Dict, Any

class XLogger:
    """统一日志处理类"""
    callbacks = []
    log_history = []
    max_history = 1000
    
    @classmethod
    def add_callback(cls, callback: Callable):
        """添加日志回调"""
        if callback not in cls.callbacks:
            cls.callbacks.append(callback)
    
    @classmethod
    def log(cls, message: str, level: str = "INFO"):
        """记录日志"""
        # 格式化日志
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        formatted_msg = f"[X² Launcher][{timestamp}][{level}] {message}"
        
        # 打印到控制台
        print(formatted_msg)
        
        # 创建日志条目
        log_entry = {
            "time": timestamp,
            "message": message,
            "type": level,
            "source": "system"
        }
        
        # 保存到历史记录
        cls.log_history.append(log_entry)
        if len(cls.log_history) > cls.max_history:
            cls.log_history = cls.log_history[-cls.max_history:]
        
        # 调用所有回调
        for callback in cls.callbacks:
            try:
                # 统一传递一个参数
                callback(log_entry)
            except Exception as e:
                print(f"日志回调异常: {e}")
    
    @classmethod
    def get_log_history(cls) -> List[Dict[str, Any]]:
        """获取日志历史记录"""
        return cls.log_history

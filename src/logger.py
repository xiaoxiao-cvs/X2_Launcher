import logging
from typing import Callable, List
from datetime import datetime

class XDeployLogger:
    def __init__(self, app_name: str = "X² Launcher"):
        self.app_name = app_name
        self.callbacks: List[Callable] = []
        self._setup_logging()
    
    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format=f'[{self.app_name}][%(asctime)s.%(msecs)03d][%(levelname)s] %(message)s',
            datefmt='%H:%M:%S'
        )
    
    def log(self, message: str, level: str = "INFO"):
        """统一的日志记录方法"""
        now = datetime.now()
        timestamp = now.strftime("%H:%M:%S.%f")[:-3]
        log_message = f"[{self.app_name}][{timestamp}][{level}] {message}"
        
        # 写入系统日志
        getattr(logging, level.lower())(message)
        
        # 触发回调
        for callback in self.callbacks:
            try:
                callback(log_message, level)
            except Exception as e:
                print(f"日志回调异常: {e}")
    
    def add_callback(self, callback: Callable):
        if callback not in self.callbacks:
            self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable):
        if callback in self.callbacks:
            self.callbacks.remove(callback)

# 全局单例
XLogger = XDeployLogger()

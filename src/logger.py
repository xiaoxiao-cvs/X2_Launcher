import logging
from typing import Callable, List
from datetime import datetime

class LogHandler:
    def __init__(self, log_file: str = "deploy.log"):
        self.callbacks: List[Callable] = []
        self._setup_logging(log_file)
    
    def _setup_logging(self, log_file: str):
        """配置日志系统"""
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def add_callback(self, callback: Callable[[str, str], None]):
        """添加日志回调函数"""
        if callback not in self.callbacks:
            self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable):
        """移除日志回调函数"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def log(self, message: str, level: str = "INFO", **kwargs):
        """记录日志并触发回调"""
        # 添加时间戳
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        # 记录到文件
        logging.log(getattr(logging, level), message)
        
        # 触发所有回调
        for callback in self.callbacks:
            try:
                callback(formatted_message, level)
            except Exception as e:
                logging.error(f"日志回调执行失败: {e}")

# 全局日志处理器实例
logger = LogHandler()

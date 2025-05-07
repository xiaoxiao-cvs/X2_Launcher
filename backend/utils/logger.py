import sys
import os
import logging
import datetime
import io

class XLogger:
    """统一的日志处理器"""
    
    LOG_DIR = "logs"
    LOG_FILE = os.path.join(LOG_DIR, f"app_{datetime.datetime.now().strftime('%Y%m%d')}.log")
    LOG_LEVEL = logging.INFO
    
    # 确保日志目录存在
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    # 配置基本日志系统
    logging.basicConfig(
        filename=LOG_FILE,
        level=LOG_LEVEL,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 日志历史记录
    _log_history = []
    # 回调函数列表
    _callbacks = []
    
    @classmethod
    def log(cls, message, level="INFO"):
        """记录日志消息"""
        # 处理编码问题，确保正确处理中文
        try:
            level = level.upper()
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            formatted_msg = f"[{level}] {message}"
            
            # 添加到历史记录
            log_entry = {
                "time": timestamp,
                "level": level,
                "message": message
            }
            cls._log_history.append(log_entry)
            
            # 限制历史记录大小
            if len(cls._log_history) > 1000:
                cls._log_history = cls._log_history[-900:]
            
            # 写入标准日志
            getattr(logging, level.lower(), logging.info)(message)
            
            # 安全地打印到控制台，处理编码问题
            if sys.stdout.encoding is None or sys.stdout.encoding.lower() != 'utf-8':
                print(formatted_msg.encode('utf-8', errors='replace').decode(sys.stdout.encoding or 'ascii', errors='replace'))
            else:
                print(formatted_msg)
            
            # 通知回调
            for callback in cls._callbacks:
                try:
                    callback(log_entry)
                except Exception as e:
                    print(f"回调错误: {str(e)}")
            
            return True
        except Exception as e:
            print(f"日志错误: {str(e)}")
            return False
    
    @classmethod
    def get_log_history(cls):
        """获取日志历史记录"""
        return cls._log_history.copy()
    
    @classmethod
    def add_callback(cls, callback):
        """添加回调函数"""
        if callback not in cls._callbacks:
            cls._callbacks.append(callback)

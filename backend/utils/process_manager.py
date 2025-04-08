import os
import sys
import subprocess
import threading
import signal
from typing import List, Dict, Any, Optional, Callable, Iterator, Union
import psutil
from pathlib import Path
from .logger import XLogger

class ProcessManager:
    """简化的进程管理器类"""
    def __init__(self):
        self.active_processes: Dict[int, subprocess.Popen] = {}
        self.base_path = Path(__file__).parent.parent
        XLogger.log("初始化进程管理器")

    def run_command(
        self,
        command: Union[str, List[str]],
        cwd: Optional[str] = None,
        shell: bool = False,
        env: Optional[Dict] = None,
        realtime_output: bool = False
    ) -> Iterator[str]:
        """执行命令并返回输出迭代器"""
        try:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=env or os.environ.copy(),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                shell=shell,
                text=True
            )
            
            self.active_processes[process.pid] = process
            
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line and realtime_output:
                    yield line.rstrip()
                    
            if process.returncode != 0:
                XLogger.log(f"命令执行失败: {command}", "ERROR")
                
            del self.active_processes[process.pid]
                
        except Exception as e:
            XLogger.log(f"命令执行异常: {e}", "ERROR")
            raise

    def run_with_callback(self, cmd: List[str], cwd: str = None, 
                          callback: Callable[[str], None] = None) -> subprocess.Popen:
        """
        运行命令并使用回调处理输出
        
        Args:
            cmd: 命令列表
            cwd: 工作目录
            callback: 输出处理回调函数
            
        Returns:
            subprocess.Popen 对象
        """
        def reader_thread(stream, callback_func):
            for line in iter(stream.readline, b''):
                if callback_func:
                    callback_func(line.decode('utf-8', errors='replace').strip())
            stream.close()
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # 创建读取线程
            stdout_thread = threading.Thread(
                target=reader_thread, 
                args=(process.stdout, callback)
            )
            stderr_thread = threading.Thread(
                target=reader_thread, 
                args=(process.stderr, callback)
            )
            
            stdout_thread.daemon = True
            stderr_thread.daemon = True
            stdout_thread.start()
            stderr_thread.start()
            
            # 记录进程
            self.active_processes[process.pid] = process
            
            return process
            
        except Exception as e:
            if callback:
                callback(f"启动进程失败: {str(e)}")
            raise e

    def kill_process_tree(self, pid: int) -> bool:
        """终止进程树"""
        try:
            # 使用psutil获取完整的进程树
            parent = psutil.Process(pid)
            
            # 先通过向子进程发送终止信号
            for child in parent.children(recursive=True):
                try:
                    child.terminate()
                except:
                    pass
            
            # 终止父进程
            parent.terminate()
            
            # 等待进程结束，如果超时则强制结束
            gone, alive = psutil.wait_procs([parent], timeout=3)
            
            if alive:
                # 如果进程仍然存活，发送kill信号
                for p in alive:
                    try:
                        p.kill()
                    except:
                        pass
            
            # 如果进程在进程记录中，移除它
            if pid in self.active_processes:
                del self.active_processes[pid]
                
            return True
        
        except Exception as e:
            XLogger.log(f"终止进程失败: {e}", "ERROR")
            return False

    def cleanup(self):
        """清理所有活动进程"""
        for pid in list(self.active_processes.keys()):
            self.kill_process_tree(pid)
        self.active_processes.clear()
        XLogger.log("已清理所有进程", "INFO")

import os
import sys
import signal
import psutil
import subprocess
import logging
from typing import Generator, Tuple, Optional, List
from .logger import logger

class ProcessManager:
    def __init__(self):
        self.active_processes = {}

    def run_command(
        self, 
        cmd: List[str], 
        cwd: Optional[str] = None, 
        realtime_output: bool = False
    ) -> Generator[str, None, None]:
        """执行命令并实时返回输出"""
        try:
            process = subprocess.Popen(
                cmd,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            self.active_processes[process.pid] = process
            
            # 实时读取输出
            while True:
                # 读取一行输出
                output = process.stdout.readline() if process.stdout else ''
                error = process.stderr.readline() if process.stderr else ''
                
                # 如果都没有输出且进程结束，就退出循环
                if not output and not error and process.poll() is not None:
                    break
                    
                # 返回输出
                if output:
                    yield output.strip()
                if error:
                    yield f"ERROR: {error.strip()}"
                    
            # 检查最终状态
            if process.poll() != 0:
                remaining_error = process.stderr.read() if process.stderr else ''
                if remaining_error:
                    yield f"ERROR: {remaining_error.strip()}"
            
            # 等待进程完成
            process.wait()
            
        except Exception as e:
            yield f"ERROR: 命令执行失败: {str(e)}"
        finally:
            if process.pid in self.active_processes:
                del self.active_processes[process.pid]

    def kill_process_tree(self, pid: int) -> bool:
        """终止进程树"""
        try:
            if os.name == 'nt':
                parent = psutil.Process(pid)
                for child in parent.children(recursive=True):
                    try:
                        child.kill()
                    except psutil.NoSuchProcess:
                        pass
                parent.kill()
            else:
                os.killpg(os.getpgid(pid), signal.SIGTERM)
            return True
            
        except (psutil.NoSuchProcess, ProcessLookupError):
            return True
        except Exception as e:
            logger.log(f"进程终止失败: {e}", "ERROR")
            return False

    def cleanup(self):
        """清理所有活动进程"""
        for pid in list(self.active_processes.keys()):
            self.kill_process_tree(pid)
        self.active_processes.clear()

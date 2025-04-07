import os
import sys
import signal
import psutil
import subprocess
import logging
from typing import Generator, Tuple, Optional
from .logger import logger

class ProcessManager:
    def __init__(self):
        self.active_processes = {}

    def run_command(
        self, 
        cmd: list, 
        cwd: str = None, 
        realtime_output: bool = False
    ) -> Generator[str, None, int] | Tuple[bool, str]:
        """执行命令并处理输出"""
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
            
            if realtime_output:
                return self._handle_realtime_output(process)
            else:
                return self._handle_normal_output(process)
                
        except Exception as e:
            logger.log(f"命令执行失败: {e}", "ERROR")
            return (False, str(e))
        finally:
            if process.pid in self.active_processes:
                del self.active_processes[process.pid]

    def _handle_realtime_output(self, process: subprocess.Popen) -> Generator[str, None, int]:
        """处理实时输出"""
        try:
            while True:
                stdout_line = process.stdout.readline()
                stderr_line = process.stderr.readline()
                
                if stdout_line:
                    yield stdout_line.strip()
                if stderr_line:
                    yield f"ERROR: {stderr_line.strip()}"
                    
                if not stdout_line and not stderr_line and process.poll() is not None:
                    break
                    
            return process.returncode
            
        except Exception as e:
            logger.log(f"输出处理失败: {e}", "ERROR")
            return 1

    def _handle_normal_output(self, process: subprocess.Popen) -> Tuple[bool, str]:
        """处理普通输出"""
        try:
            stdout, stderr = process.communicate()
            success = process.returncode == 0
            output = stdout if success else stderr
            return success, output.strip()
            
        except Exception as e:
            logger.log(f"输出处理失败: {e}", "ERROR")
            return False, str(e)

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

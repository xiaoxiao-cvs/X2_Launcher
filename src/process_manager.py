import os
import sys
import signal
import psutil
import subprocess
import logging
from typing import Generator, Tuple, Optional, List, Union, Iterator
from .logger import logger

class ProcessManager:
    def __init__(self):
        self.active_processes = {}

    @staticmethod
    def run_command(
        command: Union[str, List[str]], 
        cwd: Optional[str] = None, 
        realtime_output: bool = False,
        shell: bool = False
    ) -> Iterator[str]:
        """
        执行命令并支持实时输出
        
        Args:
            command: 要执行的命令，可以是字符串或列表
            cwd: 工作目录
            realtime_output: 是否实时输出
            shell: 是否使用shell执行
            
        Yields:
            命令的输出行
        """
        try:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                shell=shell,
                bufsize=1
            )

            # 实时读取输出
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    yield line.rstrip()

            # 获取剩余输出
            remaining_output = process.stdout.read()
            if remaining_output:
                for line in remaining_output.splitlines():
                    yield line.rstrip()

            if process.returncode != 0:
                raise subprocess.CalledProcessError(
                    process.returncode, 
                    command
                )

        except Exception as e:
            yield f"命令执行失败: {str(e)}"
            raise

    @staticmethod
    def kill_process_tree(pid: int) -> bool:
        """
        终止进程及其所有子进程
        
        Args:
            pid: 进程ID
            
        Returns:
            bool: 是否成功终止
        """
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            
            # 先终止子进程
            for child in children:
                try:
                    if os.name == 'nt':
                        child.kill()
                    else:
                        os.kill(child.pid, signal.SIGTERM)
                except psutil.NoSuchProcess:
                    pass
            
            # 终止父进程
            if os.name == 'nt':
                parent.kill()
            else:
                os.kill(pid, signal.SIGTERM)
                
            return True
        except psutil.NoSuchProcess:
            return True  # 进程已经不存在，视为成功
        except Exception:
            return False

    def cleanup(self):
        """清理所有活动进程"""
        for pid in list(self.active_processes.keys()):
            self.kill_process_tree(pid)
        self.active_processes.clear()

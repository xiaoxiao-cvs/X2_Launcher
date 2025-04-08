import os
import sys
import subprocess
from typing import Dict, List, Union, Iterator, Optional
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

    def kill_process_tree(self, pid: int) -> bool:
        """终止进程树"""
        try:
            process = self.active_processes.get(pid)
            if process:
                process.kill()
                if sys.platform == 'win32':
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(pid)], 
                                check=False, capture_output=True)
                del self.active_processes[pid]
                return True
            return False
        except Exception as e:
            XLogger.log(f"终止进程失败: {e}", "ERROR")
            return False

    def cleanup(self):
        """清理所有活动进程"""
        for pid in list(self.active_processes.keys()):
            self.kill_process_tree(pid)
        self.active_processes.clear()
        XLogger.log("已清理所有进程", "INFO")

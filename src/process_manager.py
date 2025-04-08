import os
import sys
import subprocess
from typing import Dict, List, Union, Iterator, Optional
from pathlib import Path
from .logger import XLogger
from .errors import ProcessError

# 尝试导入psutil,如果失败则使用基础进程管理
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    XLogger.log("未能导入psutil,将使用基础进程管理", "WARNING")

class ProcessManager:
    """进程管理器类"""
    def __init__(self):
        self.active_processes: Dict[int, subprocess.Popen] = {}
        self.base_path = Path(__file__).parent.parent
        XLogger.log("初始化进程管理器")

    def run_command(
        self,
        command: Union[str, List[str]],
        cwd: Optional[str] = None,
        shell: bool = False,
        env: Optional[Dict] = None
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
                if line:
                    yield line.rstrip()
                    
            if process.returncode != 0:
                raise ProcessError(f"命令执行失败: {command}")
                
            del self.active_processes[process.pid]
                
        except Exception as e:
            XLogger.log(f"命令执行异常: {e}", "ERROR")
            raise ProcessError(str(e))

    def kill_process_tree(self, pid: int) -> bool:
        """终止进程树"""
        if HAS_PSUTIL:
            try:
                process = psutil.Process(pid)
                children = process.children(recursive=True)
                
                for child in children:
                    try:
                        child.terminate()
                    except psutil.NoSuchProcess:
                        pass
                        
                process.terminate()
                
                # 等待进程结束
                _, alive = psutil.wait_procs([process, *children], timeout=3)
                for p in alive:
                    p.kill()
                    
                return True
            except Exception as e:
                XLogger.log(f"终止进程失败: {e}", "ERROR")
                return False
        else:
            # 基础进程终止方案
            try:
                if sys.platform == 'win32':
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(pid)], 
                                check=False, capture_output=True)
                else:
                    os.kill(pid, 15)  # SIGTERM
                    os.waitpid(pid, 0)
                return True
            except Exception as e:
                XLogger.log(f"基础进程终止失败: {e}", "ERROR")
                return False

    def cleanup(self):
        """清理所有活动进程"""
        for pid in list(self.active_processes.keys()):
            self.kill_process_tree(pid)
        self.active_processes.clear()
        XLogger.log("已清理所有进程", "INFO")

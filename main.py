import os
import sys
from pathlib import Path
import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import signal
import atexit
import psutil
import socket
import time
import tempfile
import platform

if platform.system() == 'Windows':
    try:
        import win32event
        import win32api
        import winerror  # 确保在Windows平台下导入
        USING_WINDOWS_MUTEX = True
    except ImportError:
        USING_WINDOWS_MUTEX = False
else:
    USING_WINDOWS_MUTEX = False

# 确保项目根目录在Python路径中
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from src.utils import setup_environment, check_network
from src.auth import GitHubAuth
from src.logger import XLogger
from src.settings import AppConfig as Settings
from src.version_manager import VersionController
from src.utils.network import find_available_port

# 进程锁定文件
LOCK_FILE = BASE_DIR / "instance.lock"
MUTEX_NAME = "Global\\X2_Launcher_Instance_Mutex"
mutex_handle = None

import subprocess  # 显式导入subprocess模块，用于执行外部命令

# Windows平台特定功能初始化
USING_WINDOWS_MUTEX = False
if platform.system() == 'Windows':
    try:
        # 检查Python安装路径
        python_path = sys.executable
        site_packages = os.path.join(os.path.dirname(python_path), 'Lib', 'site-packages')
        win32_path = os.path.join(site_packages, 'win32')
        
        # 将win32路径添加到系统路径
        if os.path.exists(win32_path) and win32_path not in sys.path:
            sys.path.append(win32_path)
            XLogger.log(f"添加win32路径: {win32_path}", "INFO")
            
        # 尝试导入
        try:
            import win32api
            import win32event
            import winerror
            
            # 验证模块是否可用
            test_mutex = win32event.CreateMutex(None, 1, "TestMutex")
            if test_mutex:
                win32api.CloseHandle(test_mutex)
                USING_WINDOWS_MUTEX = True
                XLogger.log("Windows互斥锁功能已启用", "INFO")
        except ImportError as ie:
            XLogger.log(f"win32模块导入失败: {ie}", "WARNING")
            XLogger.log(f"搜索路径: {sys.path}", "DEBUG")
            # 尝试运行注册脚本
            try:
                reg_cmd = f'"{python_path}" -m pip install --force-reinstall pywin32'
                XLogger.log(f"正在重新注册: {reg_cmd}", "INFO")
                subprocess.run(reg_cmd, shell=True, check=True)
                XLogger.log("pywin32重新注册完成，请重启应用", "INFO")
            except Exception as e:
                XLogger.log(f"注册失败: {e}", "ERROR")
    except Exception as e:
        XLogger.log(f"Windows功能初始化失败: {e}", "ERROR")
        XLogger.log(f"Python路径: {sys.executable}", "DEBUG")
        XLogger.log(f"系统信息: {platform.platform()}", "DEBUG")

def acquire_lock():
    """获取应用实例锁"""
    global mutex_handle
    try:
        if USING_WINDOWS_MUTEX:
            try:
                mutex_handle = win32event.CreateMutex(None, 1, MUTEX_NAME)
                if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
                    return False
                return True
            except:
                return _acquire_file_lock()
        else:
            return _acquire_file_lock()
    except Exception as e:
        XLogger.log(f"获取实例锁失败: {e}", "ERROR")
        return False

def _acquire_file_lock():
    """使用文件锁进行进程锁定"""
    try:
        if LOCK_FILE.exists():
            try:
                with open(LOCK_FILE, 'r') as f:
                    old_pid = int(f.read().strip())
                if psutil.pid_exists(old_pid):
                    return False
            except:
                pass
                
        with open(LOCK_FILE, 'w') as f:
            f.write(str(os.getpid()))
        return True
    except Exception as e:
        XLogger.log(f"文件锁获取失败: {e}", "ERROR")
        return False

def release_lock():
    """释放应用实例锁"""
    global mutex_handle
    try:
        if USING_WINDOWS_MUTEX and mutex_handle:
            win32api.CloseHandle(mutex_handle)
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
    except:
        pass

# 创建FastAPI应用
app = FastAPI()
settings = Settings()
config = Settings.load_config()  # 这里返回的是字典
version_controller = VersionController({
    "github_token": config.get("github_token"),
    "default_version": config.get("default_version", "latest")
})

# 配置CORS - 添加Electron支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "app://*", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载前端静态文件
frontend_path = BASE_DIR / "frontend" / "dist"
if (frontend_path.exists()):
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")

@app.get("/")
async def root():
    """根路由重定向到前端页面"""
    return RedirectResponse(url="/index.html")

@app.get("/api/versions")
async def get_versions():
    return {"versions": version_controller.get_versions()}

@app.post("/api/deploy/{version}")
async def deploy_version(version: str):
    success = version_controller.clone_version(version)
    return {"success": success}

@app.post("/api/start/{version}")
async def start_bot(version: str):
    success = version_controller.start_bot(version)
    return {"success": success}

@app.post("/api/stop")
async def stop_bot():
    success = version_controller.stop_bot()
    return {"success": success}

def cleanup_handler(signum=None, frame=None):
    """清理进程的处理函数"""
    try:
        if version_controller:
            version_controller.stop_bot()
    except Exception as e:
        XLogger.log(f"清理进程时出错: {e}", "ERROR")
    finally:
        release_lock()

# 注册清理函数
atexit.register(cleanup_handler)
signal.signal(signal.SIGINT, cleanup_handler)
signal.signal(signal.SIGTERM, cleanup_handler)

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def check_instance():
    """检查是否已有实例运行"""
    try:
        current_pid = os.getpid()
        current_script = Path(__file__).resolve()
        script_name = current_script.name.lower()
        instance_running = False
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.pid == current_pid:
                    continue
                
                if 'python' not in proc.name().lower():
                    continue
                    
                cmdline = proc.cmdline()
                if len(cmdline) < 2:
                    continue
                
                try:
                    proc_script = Path(cmdline[1]).resolve()
                except:
                    continue
                    
                if proc_script.name.lower() == script_name:
                    instance_running = True
                    XLogger.log(f"发现运行中的实例 (PID: {proc.pid})", "INFO")
                    # try:
                    #     proc.terminate()
                    #     gone, alive = psutil.wait_procs([proc], timeout=3)
                    #     if alive:
                    #         proc.kill()
                    # except psutil.NoSuchProcess:
                    #     pass
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
            except Exception as e:
                XLogger.log(f"进程检查异常: (pid={getattr(proc, 'pid', '?')}, name='{getattr(proc, 'name', lambda: '?')()}')", "WARNING")
                continue
                
        if instance_running:
            XLogger.log("等待旧实例清理...", "INFO")
            time.sleep(2)
            
        return True
            
    except Exception as e:
        XLogger.log(f"进程检查失败: {e}", "ERROR")
        return False

def setup_app():
    """应用初始化"""
    async def startup():
        XLogger.log("正在初始化环境...", "INFO")
        await setup_environment()
        
    async def shutdown():
        XLogger.log("正在清理资源...", "INFO")
        cleanup_handler()
        
    return {
        "startup": startup,
        "shutdown": shutdown
    }

if __name__ == "__main__":
    try:
        if not acquire_lock():
            XLogger.log("已有实例正在运行", "ERROR")
            sys.exit(1)
            
        if not check_instance():
            release_lock()
            sys.exit(1)
            
        port = find_available_port()
        XLogger.log(f"启动后端服务，端口: {port}", "INFO")
        
        # 配置应用生命周期
        app_handlers = setup_app()
        app.add_event_handler("startup", app_handlers["startup"])
        app.add_event_handler("shutdown", app_handlers["shutdown"])
        
        # 启动服务
        uvicorn.run(
            app, 
            host="127.0.0.1", 
            port=port,
            log_level="info",
            access_log=False,
            timeout_keep_alive=30
        )
    except SystemExit:
        release_lock()
        sys.exit(0)  # 确保正常退出
    except Exception as e:
        XLogger.log(f"启动失败: {e}", "ERROR")
        release_lock()
        sys.exit(1)
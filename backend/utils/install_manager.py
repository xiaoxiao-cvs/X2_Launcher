import os
import sys
import subprocess
import re
import json
import time
import asyncio
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any

from .logger import XLogger
from .process_manager import ProcessManager

# 尝试导入可选依赖
try:
    import aiohttp
except ImportError:
    aiohttp = None

try:
    import tomli
    import tomli_w
    TOML_SUPPORT = True
except ImportError:
    TOML_SUPPORT = False

class InstallManager:
    """安装管理器类，用于安装和配置NapCat和NoneBot"""
    
    def __init__(self):
        self.process = ProcessManager()
        self.logger = XLogger
        self.base_path = Path(__file__).parent.parent.parent
        
        # 检查依赖
        self._check_dependencies()
        
        # 安装路径
        self.napcat_path = self.base_path / "napcat"
        self.nonebot_path = self.base_path / "nonebot"
        
        # 下载URL
        self.napcat_url = "https://github.com/w4123/NapCat-QQ/releases/download/0.0.3/napcat-windows-x64.zip"
        self.nonebot_url = "https://github.com/nonebot/nonebot2/archive/refs/tags/v2.0.0.zip"
        
        # 安装标志
        self.napcat_installing = False
        self.nonebot_installing = False
        
        # 安装回调
        self.install_callback = None
    
    def _check_dependencies(self):
        """检查依赖项是否满足"""
        missing_deps = []
        
        if aiohttp is None:
            missing_deps.append("aiohttp")
        
        if not TOML_SUPPORT:
            missing_deps.append("tomli")
            missing_deps.append("tomli_w")
        
        if missing_deps:
            self._install_dependencies(missing_deps)
    
    def _install_dependencies(self, packages):
        """安装缺失的依赖"""
        try:
            self.logger.log(f"正在安装缺失的依赖: {', '.join(packages)}")
            
            # 创建进程安装依赖
            cmd = [sys.executable, "-m", "pip", "install", "--upgrade"]
            cmd.extend(packages)
            cmd.extend(["-i", "https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple"])
            
            # 执行安装
            for output in self.process.run_command(cmd, realtime_output=True):
                self.logger.log(output)
            
            self.logger.log("依赖安装完成，请重启应用")
            
            # 添加导入提示
            self.logger.log("重新导入依赖...")
            if "tomli" in packages:
                global tomli, tomli_w, TOML_SUPPORT
                import tomli
                import tomli_w
                TOML_SUPPORT = True
                
            if "aiohttp" in packages:
                global aiohttp
                import aiohttp
                
            self.logger.log("依赖导入成功")
        except Exception as e:
            self.logger.log(f"依赖安装失败: {e}", "ERROR")
            # 提供手动安装指南
            self.logger.log("请手动运行以下命令安装依赖:")
            self.logger.log(f"pip install {' '.join(packages)} -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple")
        
    def set_install_callback(self, callback: Callable):
        """设置安装回调函数"""
        self.install_callback = callback
        
    def _log(self, message: str, level: str = "INFO", source: str = "install"):
        """记录日志"""
        self.logger.log(message, level)
        if self.install_callback:
            self.install_callback({
                "message": message,
                "level": level,
                "source": source,
                "time": time.strftime("%Y-%m-%d %H:%M:%S")
            })
    
    def is_valid_qq(self, qq_str):
        """检查是否为有效的QQ号"""
        return bool(re.match(r'^\d+$', qq_str))
            
    def create_napcat_config(self, qq_number):
        """创建NapCat配置文件"""
        self._log(f"正在为QQ {qq_number} 创建NapCat配置...")
        
        config = {
            "fileLog": False,
            "consoleLog": True,
            "fileLogLevel": "debug",
            "consoleLogLevel": "info",
            "packetBackend": "auto",
            "packetServer": "",
            "o3HookMode": 1
        }
        
        # 确保目录存在
        config_dir = self.napcat_path / "versions/9.9.18-32793/resources/app/napcat/config"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建配置文件
        config_path = config_dir / f'napcat_{qq_number}.json'
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
            
        self._log(f"NapCat配置已创建: {config_path}")
        return True

    def create_onebot_config(self, qq_number):
        """创建OneBot11配置文件"""
        self._log(f"正在为QQ {qq_number} 创建OneBot配置...")
        
        config = {
            "network": {
                "httpServers": [],
                "httpSseServers": [],
                "httpClients": [],
                "websocketServers": [
                    {
                        "enable": True,
                        "name": "MaiBot Main",
                        "host": "0.0.0.0",
                        "port": 8095,
                        "reportSelfMessage": False,
                        "enableForcePushEvent": True,
                        "messagePostFormat": "array",
                        "token": "",
                        "debug": False,
                        "heartInterval": 30000
                    }
                ],
                "websocketClients": [],
                "plugins": []
            },
            "musicSignUrl": "",
            "enableLocalFile2Url": False,
            "parseMultMsg": False
        }
        
        # 确保目录存在
        config_dir = self.napcat_path / "versions/9.9.18-32793/resources/app/napcat/config"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建配置文件
        config_path = config_dir / f'onebot11_{qq_number}.json'
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
            
        self._log(f"OneBot配置已创建: {config_path}")
        return True

    def update_qq_in_config(self, path_str: str, qq_number: int):
        """更新配置文件中的QQ号"""
        if not TOML_SUPPORT:
            self._log("缺少TOML支持，请安装tomli和tomli_w依赖", "ERROR")
            return False
            
        self._log(f"正在更新配置文件: {path_str} 中的QQ号为 {qq_number}...")
        
        config_path = Path(path_str)
        
        # 确保目录存在
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 如果文件不存在，创建模板
        if not config_path.exists():
            self._log(f"配置文件不存在，创建模板: {config_path}")
            default_config = """[bot]
# qq账号
qq = 123456789
# 密码，可为空，需要时会让你扫码登录
password = ""
# 登录协议 ikun_ws pad android watch
# 目前ikun_ws协议支持最全
protocol = "ikun_ws"
# NapCat的websocket地址
universal = ["ws://127.0.0.1:8095"]

[bots]
[[bots.admins]]
# 主人qq account
account = 123456789
# 权限等级
level = 5
"""
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(default_config)
        
        # 读取原始文件内容
        with open(config_path, 'rb') as f:
            try:
                config = tomli.load(f)
            except Exception as e:
                self._log(f"读取TOML配置失败: {e}", "ERROR")
                return False
        
        # 只更新qq值
        config['bot']['qq'] = int(qq_number)
        
        # 读取原始文件内容以保留注释
        with open(config_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # 使用正则表达式替换qq值，保留其他内容和注释
        updated_content = re.sub(
            r'(\[bot\][^\[]*qq\s*=\s*)\d+',
            f'\g<1>{qq_number}',
            original_content
        )
        
        # 写入更新后的内容
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
            
        self._log(f"配置文件已更新: {config_path}")
        return True
        
    async def download_file(self, url: str, save_path: Path, source_label: str):
        """下载文件"""
        if aiohttp is None:
            self._log("缺少aiohttp依赖，无法下载文件", "ERROR")
            return False
            
        self._log(f"正在从 {url} 下载 {source_label}...")
        
        # 确保目录存在
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    total_size = int(response.headers.get('content-length', 0))
                    
                    with open(save_path, 'wb') as fd:
                        downloaded = 0
                        start_time = time.time()
                        
                        async for chunk in response.content.iter_chunked(1024):
                            fd.write(chunk)
                            downloaded += len(chunk)
                            
                            # 计算进度和速度
                            elapsed = time.time() - start_time
                            if elapsed > 0:
                                speed = downloaded / elapsed / 1024  # KB/s
                                percent = int(downloaded * 100 / total_size) if total_size > 0 else 0
                                
                                # 每5%报告一次进度
                                if percent % 5 == 0:
                                    self._log(
                                        f"{source_label} 下载进度: {percent}% ({self._format_size(downloaded)}/{self._format_size(total_size)}) - {speed:.1f} KB/s",
                                        source=source_label.lower()
                                    )
            
            self._log(f"{source_label} 下载完成: {save_path}", source=source_label.lower())
            return True
            
        except Exception as e:
            self._log(f"{source_label} 下载失败: {e}", "ERROR", source=source_label.lower())
            return False
    
    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes/1024:.1f} KB"
        else:
            return f"{size_bytes/(1024*1024):.1f} MB"
    
    async def extract_zip(self, zip_path: Path, extract_to: Path, name: str):
        """解压ZIP文件"""
        self._log(f"正在解压 {name}...")
        
        try:
            import zipfile
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # 计算总文件数
                total_files = len(zip_ref.namelist())
                extracted = 0
                
                for file in zip_ref.namelist():
                    zip_ref.extract(file, extract_to)
                    extracted += 1
                    
                    # 每10%报告一次进度
                    percent = int(extracted * 100 / total_files)
                    if percent % 10 == 0:
                        self._log(f"{name} 解压进度: {percent}%", source=name.lower())
            
            self._log(f"{name} 解压完成", source=name.lower())
            return True
            
        except Exception as e:
            self._log(f"{name} 解压失败: {e}", "ERROR", source=name.lower())
            return False
    
    async def install_napcat(self, qq_number: str):
        """安装NapCat"""
        if not self.is_valid_qq(qq_number):
            self._log(f"无效的QQ号: {qq_number}", "ERROR", "napcat")
            return False
            
        if self.napcat_installing:
            self._log("NapCat正在安装中，请等待...", "WARNING", "napcat")
            return False
        
        # 检查依赖
        if aiohttp is None:
            self._log("缺少aiohttp依赖，无法下载NapCat", "ERROR", "napcat")
            return False
        
        self.napcat_installing = True
        
        try:
            # 下载NapCat
            zip_path = self.base_path / "downloads" / "napcat.zip"
            success = await self.download_file(self.napcat_url, zip_path, "NapCat")
            if not success:
                return False
            
            # 创建安装目录
            self.napcat_path.mkdir(parents=True, exist_ok=True)
            
            # 解压NapCat
            success = await self.extract_zip(zip_path, self.napcat_path, "NapCat")
            if not success:
                return False
            
            # 创建配置
            self.create_napcat_config(qq_number)
            self.create_onebot_config(qq_number)
            
            self._log(f"NapCat安装成功，QQ: {qq_number}", "SUCCESS", "napcat")
            return True
            
        except Exception as e:
            self._log(f"NapCat安装失败: {e}", "ERROR", "napcat")
            return False
            
        finally:
            self.napcat_installing = False
    
    async def install_nonebot(self, qq_number: str):
        """安装NoneBot"""
        if not self.is_valid_qq(qq_number):
            self._log(f"无效的QQ号: {qq_number}", "ERROR", "nonebot")
            return False
            
        if self.nonebot_installing:
            self._log("NoneBot正在安装中，请等待...", "WARNING", "nonebot")
            return False
        
        # 检查TOML支持
        if not TOML_SUPPORT:
            self._log("缺少TOML支持，无法配置NoneBot", "ERROR", "nonebot")
            return False
        
        self.nonebot_installing = True
        
        try:
            # 创建配置目录
            config_dir = self.base_path / "maibot_versions" / "config"
            config_dir.mkdir(parents=True, exist_ok=True)
            template_dir = self.base_path / "maibot_versions" / "template"
            template_dir.mkdir(parents=True, exist_ok=True)
            
            # 更新QQ配置
            self.update_qq_in_config(str(config_dir / "bot_config.toml"), qq_number)
            self.update_qq_in_config(str(template_dir / "bot_config_template.toml"), qq_number)
            
            self._log(f"NoneBot配置更新成功，QQ: {qq_number}", "SUCCESS", "nonebot")
            return True
            
        except Exception as e:
            self._log(f"NoneBot配置更新失败: {e}", "ERROR", "nonebot")
            return False
            
        finally:
            self.nonebot_installing = False

    def run_install_script(self, cwd: Optional[str] = None):
        """运行test.bat安装脚本"""
        self._log("开始执行安装脚本...", source="install")
        
        # 找到脚本路径
        script_path = self.base_path / "backend" / "test.bat"
        
        if not script_path.exists():
            self._log(f"安装脚本不存在: {script_path}", "ERROR", "install")
            return False
            
        try:
            # 运行批处理脚本并实时获取输出
            for output in self.process.run_command(
                [str(script_path)],
                cwd=cwd or str(self.base_path),
                shell=True,
                realtime_output=True
            ):
                self._log(output, source="install")
            
            self._log("安装脚本执行完成", "SUCCESS", "install")
            return True
            
        except Exception as e:
            self._log(f"安装脚本执行失败: {e}", "ERROR", "install")
            return False

    def run_bat_script(self, script_content: str, cwd: Optional[str] = None):
        """运行批处理脚本"""
        self._log("正在执行批处理脚本...")
        
        # 创建临时批处理文件
        bat_file = Path(self.base_path) / "temp_script.bat"
        with open(bat_file, "w", encoding="utf-8") as f:
            f.write(script_content)
        
        try:
            # 运行批处理脚本并实时获取输出
            for output in self.process.run_command(
                [bat_file],
                cwd=cwd,
                shell=True,
                realtime_output=True
            ):
                self._log(output)
            
            self._log("批处理脚本执行完成")
            return True
            
        except Exception as e:
            self._log(f"批处理脚本执行失败: {e}", "ERROR")
            return False
            
        finally:
            # 删除临时批处理文件
            if bat_file.exists():
                bat_file.unlink()

import importlib
import sys
import subprocess
import pkg_resources
from typing import Dict, List, Tuple
from .logger import XLogger

class DependencyChecker:
    """用于检查项目依赖的类"""
    
    # 必要依赖列表及其版本要求
    REQUIRED_PACKAGES = {
        "fastapi": ">=0.68.0",
        "uvicorn": ">=0.15.0",
        "aiohttp": ">=3.7.4",
        "websockets": ">=10.0",
        "tomli": ">=2.0.0",
        "requests": ">=2.25.0",
        "packaging": ">=20.0",
        "pydantic": ">=1.8.0",
        "psutil": ">=5.9.0",   # 添加系统监控所需的psutil
        "python-multipart": ">=0.0.5",  # 用于处理文件上传
    }
    
    # 可选但推荐的包
    OPTIONAL_PACKAGES = {
        "tomli_w": ">=1.0.0",
        "python-multipart": ">=0.0.5",
        "Pillow": ">=8.0.0",
    }
    
    def __init__(self):
        self.logger = XLogger
    
    def check_all_dependencies(self) -> Dict:
        """检查所有依赖库的安装情况"""
        self.logger.log("开始检查依赖...")
        
        # 基本Python信息
        result = {
            "python_version": self._get_python_version(),
            "platform": sys.platform,
            "required": self._check_packages(self.REQUIRED_PACKAGES),
            "optional": self._check_packages(self.OPTIONAL_PACKAGES),
            "pip_version": self._get_pip_version(),
            "installable": True,  # 默认为True
        }
        
        # 检查是否可以安装包
        result["installable"] = self._check_pip_installation_capability()
        
        self.logger.log("依赖检查完成")
        return result
        
    def _get_python_version(self) -> str:
        """获取Python版本"""
        return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    def _get_pip_version(self) -> str:
        """获取pip版本"""
        try:
            return pkg_resources.get_distribution("pip").version
        except pkg_resources.DistributionNotFound:
            return "未安装"
        except Exception as e:
            return f"错误: {str(e)}"
    
    def _check_packages(self, packages_dict: Dict[str, str]) -> Dict[str, Dict]:
        """检查一系列包的安装状态"""
        result = {}
        for package_name, version_req in packages_dict.items():
            status, version, message = self._check_package(package_name)
            result[package_name] = {
                "installed": status,
                "version": version,
                "message": message,
                "required_version": version_req
            }
        return result
    
    def _check_package(self, package_name: str) -> Tuple[bool, str, str]:
        """检查单个包是否安装"""
        try:
            # 尝试导入模块
            module = importlib.import_module(package_name.split('[')[0])  # 处理类似 'package[extra]' 的情况
            
            # 获取版本
            try:
                version = pkg_resources.get_distribution(package_name).version
                return True, version, "已安装"
            except pkg_resources.DistributionNotFound:
                # 模块可能是内建的或者与包名不同
                if hasattr(module, '__version__'):
                    return True, getattr(module, '__version__'), "已安装"
                else:
                    return True, "未知版本", "已安装但无法获取版本"
                
        except ImportError:
            return False, "", "未安装"
        except Exception as e:
            return False, "", f"检查错误: {str(e)}"
    
    def _check_pip_installation_capability(self) -> bool:
        """检查是否可以通过pip安装包"""
        try:
            # 尝试运行一个简单的pip命令
            result = subprocess.run(
                [sys.executable, "-m", "pip", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def install_package(self, package_name: str) -> Tuple[bool, str]:
        """尝试安装一个包"""
        self.logger.log(f"尝试安装 {package_name}...")
        
        try:
            cmd = [
                sys.executable, "-m", "pip", "install", 
                package_name,
                "-i", "https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # 给足够的时间安装
            )
            
            if result.returncode == 0:
                self.logger.log(f"{package_name} 安装成功")
                return True, f"{package_name} 安装成功"
            else:
                self.logger.log(f"{package_name} 安装失败: {result.stderr}", "ERROR")
                return False, f"安装失败: {result.stderr}"
                
        except Exception as e:
            self.logger.log(f"{package_name} 安装过程错误: {str(e)}", "ERROR")
            return False, f"安装过程错误: {str(e)}"
    
    def install_missing_dependencies(self, packages=None) -> Dict:
        """安装所有缺失的必要依赖"""
        self.logger.log("开始安装缺失的必要依赖...")
        result = {
            "overall_success": True,
            "details": {}
        }
        
        # 如果指定了包，只安装这些包
        if packages:
            for package_name in packages:
                success, message = self.install_package(package_name)
                result["details"][package_name] = {
                    "success": success,
                    "message": message
                }
                if not success:
                    result["overall_success"] = False
            return result
        
        # 否则检查所有依赖并安装缺失的
        deps = self._check_packages(self.REQUIRED_PACKAGES)
        
        # 安装缺失的依赖
        for package_name, info in deps.items():
            if not info["installed"]:
                success, message = self.install_package(package_name)
                result["details"][package_name] = {
                    "success": success,
                    "message": message
                }
                if not success:
                    result["overall_success"] = False
        
        self.logger.log("缺失依赖安装完成" if result["overall_success"] else "部分依赖安装失败")
        return result

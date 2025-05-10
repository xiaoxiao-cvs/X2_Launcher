import os
import sys
import re
import json
import shutil
import logging
import random
import subprocess
import platform  # 添加platform模块的导入
from pathlib import Path
from typing import Dict, List, Optional, Union

# 使用 tomli/tomli_w 代替 toml
try:
    import tomli as toml_reader  # 用于读取TOML
    import tomli_w as toml_writer  # 用于写入TOML
except ImportError:
    print("尝试安装缺少的TOML处理库...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "tomli", "tomli_w", "--quiet"])
        print("安装成功，正在导入...")
        import tomli as toml_reader
        import tomli_w as toml_writer
    except Exception as e:
        print(f"错误: 无法自动安装TOML处理库: {e}")
        print("请手动安装所需依赖: pip install tomli tomli_w")
        sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("MaiBot-Configurator")

class BotConfigurator:
    """MaiBot配置器，负责配置MaiBot和Adapter"""
    
    def __init__(self, base_install_dir: str, instance_name: str = "default"):
        """初始化配置器
        
        Args:
            base_install_dir: 基础安装目录 (e.g., MaiM-with-u/{instance_name})
            instance_name: 实例名称
        """
        self.base_install_dir = base_install_dir # This is MaiM-with-u/{instance_name}
        self.instance_name = instance_name
        # MaiBot program files are inside MaiBot subdirectory
        self.maibot_program_dir = os.path.join(self.base_install_dir, "MaiBot")
        
        # 适配器目录，相对于 base_install_dir
        self.adapter_dir_name = "MaiBot-Napcat-Adapter" # Default name
        self.adapter_full_path = os.path.join(self.base_install_dir, self.adapter_dir_name)
        
        self.config_dir = os.path.join(self.maibot_program_dir, "config") # MaiBot's own config dir
        self.venv_path = os.path.join(self.base_install_dir, "venv") # venv is in the instance root

        # 确保MaiBot程序目录存在
        if not os.path.exists(self.maibot_program_dir):
            logger.warning(f"MaiBot程序目录不存在: {self.maibot_program_dir}, 配置可能失败。")
            # Attempt to create it for robustness, though downloader should have done this.
            os.makedirs(self.maibot_program_dir, exist_ok=True)

        os.makedirs(self.config_dir, exist_ok=True)
        
        logger.info(f"配置器初始化 - 实例: {instance_name}")
        logger.info(f"实例根目录: {self.base_install_dir}")
        logger.info(f"MaiBot程序目录: {self.maibot_program_dir}")
        logger.info(f"预期适配器目录: {self.adapter_full_path}")
        logger.info(f"MaiBot配置目录: {self.config_dir}")
        logger.info(f"虚拟环境目录: {self.venv_path}")

    def _clone_adapter_if_needed(self):
        """如果适配器目录不存在，则尝试克隆。"""
        if not os.path.exists(self.adapter_full_path):
            logger.info(f"适配器目录 {self.adapter_full_path} 不存在，尝试克隆...")
            git_url = "https://github.com/MaiM-with-u/MaiBot-NapCat-Adapter.git"
            # Clone into self.adapter_full_path
            git_cmd = ["git", "clone", git_url, self.adapter_full_path, "--depth", "1"]
            try:
                process = subprocess.Popen(
                    git_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace'
                )
                for line in process.stdout:
                    logger.info(f"AdapterGit: {line.strip()}")
                    print(f"【AdapterGit】{line.strip()}")
                process.wait()
                if process.returncode == 0 and os.path.exists(self.adapter_full_path):
                    logger.info(f"适配器克隆成功到: {self.adapter_full_path}")
                    return True
                else:
                    logger.error(f"适配器克隆失败，返回码: {process.returncode}")
                    return False
            except Exception as e:
                logger.error(f"克隆适配器时发生异常: {e}")
                return False
        else:
            logger.info(f"适配器目录已存在: {self.adapter_full_path}")
            return True

    def configure_maibot(self, 
                        maibot_port: int = 8000, 
                        model_type: str = "chatglm") -> bool:
        """配置MaiBot
        
        Args:
            maibot_port: MaiBot监听端口
            model_type: 使用的模型类型
            
        Returns:
            bool: 是否配置成功
        """
        try:
            # 1. 配置.env文件
            env_template_path = os.path.join(self.maibot_program_dir, "template", "template.env")
            env_path = os.path.join(self.maibot_program_dir, ".env")
            
            if os.path.exists(env_template_path):
                logger.info(f"找到模板.env文件: {env_template_path}")
                with open(env_template_path, "r", encoding="utf-8") as f:
                    env_content = f.read()
                
                # 替换端口
                env_content = re.sub(r'PORT=\d+', f'PORT={maibot_port}', env_content)
                # 确保有HOST字段
                if not re.search(r'HOST=', env_content):
                    env_content += "\nHOST=0.0.0.0\n"
                else:
                    env_content = re.sub(r'HOST=.*', 'HOST=0.0.0.0', env_content)
                
                with open(env_path, "w", encoding="utf-8") as f:
                    f.write(env_content)
                logger.info(f"已配置MaiBot .env文件，设置端口为 {maibot_port}")
            else:
                logger.error(f"模板.env文件不存在: {env_template_path}")
                # 创建一个基本的.env文件
                basic_env = f"PORT={maibot_port}\nHOST=0.0.0.0\n"
                with open(env_path, "w", encoding="utf-8") as f:
                    f.write(basic_env)
                logger.info(f"没有找到模板，创建了基本的.env文件，设置端口为 {maibot_port}")
            
            # 2. 配置bot_config.toml
            config_template_path = os.path.join(self.maibot_program_dir, "template", "bot_config_template.toml")
            config_path = os.path.join(self.config_dir, "bot_config.toml")
            
            if os.path.exists(config_template_path):
                logger.info(f"找到模板配置文件: {config_template_path}")
                with open(config_template_path, "r", encoding="utf-8") as f:
                    config_content = f.read()
                
                # 添加模型配置
                if model_type == "chatglm":
                    config_content = self._add_chatglm_config(config_content)
                
                with open(config_path, "w", encoding="utf-8") as f:
                    f.write(config_content)
                logger.info("已配置MaiBot bot_config.toml文件")
            else:
                logger.error(f"模板bot_config_template.toml文件不存在: {config_template_path}")
                # 可以考虑创建一个基本的配置文件，但这里不实现，因为配置过于复杂
                return False
            
            return True
        except Exception as e:
            logger.error(f"配置MaiBot时出错：{e}")
            return False
    
    def _add_chatglm_config(self, config_content: str) -> str:
        """添加ChatGLM模型配置
        
        Args:
            config_content: 原配置文件内容
            
        Returns:
            str: 修改后的配置内容
        """
        # 如果已经有模型配置，则不修改
        if "[model]" in config_content:
            return config_content
        
        # 添加ChatGLM默认配置
        model_config = """
[model]
type = "chatglm"
remote = false
remote_url = ""

[model.prompt_template]
default = "{prompt}"
"""
        return config_content + model_config
    
    def configure_adapter(self, 
                         qq_number: str, 
                         napcat_ws_port: int, # Renamed for clarity, this is NapCat's WebSocket server port
                         adapter_listen_port: int, # Adapter's own listening port
                         maibot_api_port: int # MaiBot's API port
                         ) -> bool:
        """配置MaiBot-Napcat-Adapter
        """
        try:
            logger.info(f"开始配置Adapter: QQ={qq_number}, NapCatWS={napcat_ws_port}, AdapterListen={adapter_listen_port}, MaiBotAPI={maibot_api_port}")
            
            if not os.path.exists(self.adapter_full_path):
                logger.error(f"适配器目录不存在: {self.adapter_full_path}，无法配置。")
                return False
            
            adapter_config_path = os.path.join(self.adapter_full_path, "config.toml")
            adapter_template_path = os.path.join(self.adapter_full_path, "template", "template_config.toml")

            adapter_config = {}
            if os.path.exists(adapter_template_path):
                logger.info(f"找到适配器模板配置: {adapter_template_path}")
                shutil.copy(adapter_template_path, adapter_config_path)
                logger.info(f"已复制模板配置到: {adapter_config_path}")
                try:
                    with open(adapter_config_path, "rb") as f:
                        adapter_config = toml_reader.load(f)
                except Exception as e:
                    logger.error(f"读取适配器模板配置出错: {e}, 将使用默认值创建。")
                    adapter_config = {} # Reset if loading fails
            elif os.path.exists(adapter_config_path): # If no template, try to load existing
                 logger.info(f"适配器模板未找到，尝试加载现有配置: {adapter_config_path}")
                 try:
                    with open(adapter_config_path, "rb") as f:
                        adapter_config = toml_reader.load(f)
                 except Exception as e:
                    logger.error(f"读取现有适配器配置亦出错: {e}, 将使用默认值创建。")
                    adapter_config = {}
            else:
                logger.warning(f"适配器模板和现有配置均不存在，将创建全新配置: {adapter_config_path}")

            # Ensure sections exist
            if "Napcat_Server" not in adapter_config: adapter_config["Napcat_Server"] = {}
            if "MaiBot_Server" not in adapter_config: adapter_config["MaiBot_Server"] = {}
            if "Napcat" not in adapter_config: adapter_config["Napcat"] = {}
            if "Adapter" not in adapter_config: adapter_config["Adapter"] = {} # For adapter's own port

            # Update Napcat_Server (where adapter connects to NapCat)
            adapter_config["Napcat_Server"]["host"] = "127.0.0.1" # Typically NapCat runs locally
            adapter_config["Napcat_Server"]["port"] = napcat_ws_port
            adapter_config["Napcat_Server"]["heartbeat"] = adapter_config["Napcat_Server"].get("heartbeat", 30)

            # Update MaiBot_Server (where adapter connects to MaiBot)
            adapter_config["MaiBot_Server"]["platform_name"] = adapter_config["MaiBot_Server"].get("platform_name", "qq")
            adapter_config["MaiBot_Server"]["host"] = "127.0.0.1" # Typically MaiBot runs locally
            adapter_config["MaiBot_Server"]["port"] = maibot_api_port

            # Update Napcat (Bot's QQ info)
            adapter_config["Napcat"]["QQ"] = str(qq_number) # Ensure QQ is string
            adapter_config["Napcat"]["bot_name"] = adapter_config["Napcat"].get("bot_name", self.instance_name)
            
            # Update Adapter's own listening port
            adapter_config["Adapter"]["port"] = adapter_listen_port
            
            # Compatibility for old NoneBot section if it exists
            if "NoneBot" in adapter_config and "port" in adapter_config["NoneBot"]:
                adapter_config["NoneBot"]["port"] = adapter_listen_port
            
            with open(adapter_config_path, "wb") as f:
                toml_writer.dump(adapter_config, f)
            
            logger.info(f"已配置Adapter config.toml: {adapter_config_path}")
            return True
        except Exception as e:
            logger.error(f"配置Adapter时出错：{e}", exc_info=True)
            return False
    
    def create_napcat_config(self) -> str:
        """创建NapCat的配置说明文件
        
        Returns:
            str: 配置说明文本
        """
        napcat_config_path = os.path.join(self.base_install_dir, "napcat_config_guide.txt")
        content = """# NapCat 配置指南

在NapCat中，您需要创建一个"websocket客户端"，并按照以下设置配置它：

1. 打开NapCat管理页面
2. 添加一个新的WebSocket客户端
3. 设置反向代理URL，格式如下：
   ws://localhost:8095/

确保端口与Adapter配置中的Napcat_Server.port字段匹配。
设置心跳间隔为30000ms (30秒)。

请参考NapCat文档获取更多信息：
Shell版: https://www.napcat.wiki/guide/boot/Shell
Framework版: https://www.napcat.wiki/guide/boot/Framework
"""
        with open(napcat_config_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        logger.info(f"已创建NapCat配置指南: {napcat_config_path}")
        return content
    
    def create_startup_scripts(self, cfg: dict) -> bool:
        """创建所有相关的启动脚本
        Args:
            cfg (dict): Full configuration dictionary containing ports etc.
        Returns:
            bool: 是否创建成功
        """
        try:
            python_in_venv = os.path.join(self.venv_path, "Scripts" if platform.system() == "Windows" else "bin", "python")
            activate_script = os.path.join(self.venv_path, "Scripts" if platform.system() == "Windows" else "bin", "activate")

            # 1. MaiBot 主程序启动脚本 (app.py)
            maibot_script_filename = f"启动MaiBot_{self.instance_name}.{'bat' if platform.system() == 'Windows' else 'sh'}"
            maibot_script_path = os.path.join(self.base_install_dir, maibot_script_filename)
            
            if platform.system() == "Windows":
                maibot_script_content = f"""@echo off
title MaiBot - {self.instance_name}
echo 正在激活虚拟环境: {self.venv_path}
call "{activate_script}"
echo 切换到MaiBot程序目录: {self.maibot_program_dir}
cd /d "{self.maibot_program_dir}"
echo 正在启动MaiBot主程序 (app.py)...
"{python_in_venv}" app.py
pause
"""
            else: # Linux/macOS
                maibot_script_content = f"""#!/bin/bash
echo "正在激活虚拟环境: {self.venv_path}"
source "{activate_script}"
echo "切换到MaiBot程序目录: {self.maibot_program_dir}"
cd "{self.maibot_program_dir}"
echo "正在启动MaiBot主程序 (app.py)..."
"{python_in_venv}" app.py
"""
            with open(maibot_script_path, "w", encoding="utf-8") as f: f.write(maibot_script_content)
            if platform.system() != "Windows": os.chmod(maibot_script_path, 0o755)
            logger.info(f"已创建MaiBot启动脚本：{maibot_script_path}")

            # 2. Adapter 启动脚本 (main.py in adapter dir) - if adapter is installed
            if cfg.get("install_adapter") and os.path.exists(self.adapter_full_path):
                adapter_script_filename = f"启动Adapter_{self.instance_name}.{'bat' if platform.system() == 'Windows' else 'sh'}"
                adapter_script_path = os.path.join(self.base_install_dir, adapter_script_filename)
                if platform.system() == "Windows":
                    adapter_script_content = f"""@echo off
title MaiBot Adapter - {self.instance_name}
echo 正在激活虚拟环境: {self.venv_path}
call "{activate_script}"
echo 切换到Adapter目录: {self.adapter_full_path}
cd /d "{self.adapter_full_path}"
echo 正在启动MaiBot-Napcat-Adapter (main.py)...
"{python_in_venv}" main.py
pause
"""
                else: # Linux/macOS
                    adapter_script_content = f"""#!/bin/bash
echo "正在激活虚拟环境: {self.venv_path}"
source "{activate_script}"
echo "切换到Adapter目录: {self.adapter_full_path}"
cd "{self.adapter_full_path}"
echo "正在启动MaiBot-Napcat-Adapter (main.py)..."
"{python_in_venv}" main.py
"""
                with open(adapter_script_path, "w", encoding="utf-8") as f: f.write(adapter_script_content)
                if platform.system() != "Windows": os.chmod(adapter_script_path, 0o755)
                logger.info(f"已创建Adapter启动脚本：{adapter_script_path}")
            
            # 3. 创建启动顺序指南
            startup_guide_path = os.path.join(self.base_install_dir, f"启动说明_{self.instance_name}.txt")
            guide_content = f"""# MaiBot 实例 ({self.instance_name}) 启动说明

请按以下顺序启动各组件：

1.  启动 NapCat 服务。
    (请参考 NapCat 官方文档进行安装和启动，确保其 WebSocket 服务运行在端口 {cfg.get('ports', {}).get('napcat', '未知')})

"""
            if cfg.get("install_adapter"):
                guide_content += f"2.  运行 '{adapter_script_filename}' 启动 MaiBot-Napcat-Adapter。\n"
                guide_content += f"3.  运行 '{maibot_script_filename}' 启动 MaiBot 主程序。\n"
            else:
                 guide_content += f"2.  运行 '{maibot_script_filename}' 启动 MaiBot 主程序。\n (适配器未选择安装)\n"
            
            guide_content += """
正确的启动顺序很重要，否则各组件之间可能无法正常通信。
确保所有相关的端口没有被占用。
"""
            with open(startup_guide_path, "w", encoding="utf-8") as f: f.write(guide_content)
            logger.info(f"已创建启动说明：{startup_guide_path}")
            
            return True
        except Exception as e:
            logger.error(f"创建启动脚本时出错：{e}", exc_info=True)
            return False
    
    def verify_installation(self) -> bool:
        """验证安装是否成功
        
        Returns:
            bool: 安装是否成功
        """
        # 检查必要的目录和文件是否存在
        required_dirs = [
            self.maibot_program_dir,
            self.adapter_full_path,
            self.venv_path
        ]
        
        for dir_path in required_dirs:
            if not os.path.exists(dir_path):
                logger.error(f"目录不存在: {dir_path}")
                return False
        
        # 检查基本配置文件是否存在
        required_files = [
            os.path.join(self.maibot_program_dir, ".env"),
            os.path.join(self.config_dir, "bot_config.toml"),
            os.path.join(self.adapter_full_path, "config.toml")
        ]
        
        for file_path in required_files:
            if not os.path.exists(file_path):
                logger.warning(f"配置文件不存在: {file_path}")
                # 不返回False，因为可能有些模板不存在
        
        return True
    
    def configure(self, config_params: dict) -> dict:
        """执行完整的配置流程
        
        Args:
            config_params: 从前端传递的配置参数字典
                Expected keys: "instance_name", "qq_number", 
                               "install_napcat", "install_adapter",
                               "ports": {"maibot", "adapter", "napcat"}
                               "model_type" (optional)
        
        Returns:
            dict: 配置结果
        """
        logger.info(f"开始配置实例 {self.instance_name} 使用参数: {config_params}")

        # 验证基础目录和 MaiBot 程序目录
        if not os.path.exists(self.base_install_dir) or not os.path.exists(self.maibot_program_dir):
            msg = f"基础目录 {self.base_install_dir} 或 MaiBot程序目录 {self.maibot_program_dir} 不存在。请先完成基础部署。"
            logger.error(msg)
            return {"success": False, "message": msg}

        # 从 config_params 获取配置
        qq_number = str(config_params.get("qq_number", ""))
        ports = config_params.get("ports", {})
        maibot_port = int(ports.get("maibot", 8000))
        adapter_port = int(ports.get("adapter", 18002))
        napcat_port = int(ports.get("napcat", 8095)) # This is NapCat's WS port
        
        model_type = config_params.get("model_type", "chatglm") # Default or from params
        
        should_install_adapter = config_params.get("install_adapter", False)
        # should_install_napcat = config_params.get("install_napcat", False) # NapCat is external, we only configure for it

        # 1. 配置MaiBot (.env, bot_config.toml)
        logger.info(f"配置MaiBot核心: 端口={maibot_port}, 模型={model_type}")
        if not self.configure_maibot(maibot_port=maibot_port, model_type=model_type):
            return {"success": False, "message": "配置MaiBot核心失败"}
        
        # 2. 如果需要，克隆并配置Adapter
        if should_install_adapter:
            logger.info("需要安装/配置适配器。")
            if not self._clone_adapter_if_needed(): # Clones if not exists
                 return {"success": False, "message": "克隆MaiBot-Napcat-Adapter失败"}

            logger.info(f"配置Adapter: QQ={qq_number}, NapCatWS端口={napcat_port}, Adapter监听端口={adapter_port}, MaiBotAPI端口={maibot_port}")
            if not self.configure_adapter(
                qq_number=qq_number,
                napcat_ws_port=napcat_port,
                adapter_listen_port=adapter_port,
                maibot_api_port=maibot_port
            ):
                return {"success": False, "message": "配置Adapter失败"}
        else:
            logger.info("跳过适配器安装/配置。")

        # 3. 创建NapCat配置指南 (always useful if NapCat is involved)
        if config_params.get("install_napcat") or should_install_adapter: # If either NapCat or its adapter is chosen
            self.create_napcat_config() # This just creates a guide file

        # 4. 创建启动脚本
        logger.info("创建启动脚本...")
        if not self.create_startup_scripts(config_params): # Pass full config for script content
            # Non-critical failure, main config might be done
            logger.warning("创建启动脚本失败，但主要配置可能已完成。")
        
        logger.info(f"实例 {self.instance_name} 配置成功完成。")
        return {
            "success": True,
            "message": "配置成功完成",
            "base_dir": self.base_install_dir,
            "maibot_dir": self.maibot_program_dir,
            "adapter_dir": self.adapter_full_path if should_install_adapter else None,
            "config_summary": {
                "qq_number": qq_number,
                "ports": {"maibot": maibot_port, "adapter": adapter_port, "napcat": napcat_port},
                "adapter_installed": should_install_adapter,
                "model_type": model_type
            }
        }

if __name__ == "__main__":
    # 命令行测试用
    import argparse
    parser = argparse.ArgumentParser(description="MaiBot配置工具")
    parser.add_argument("--dir", required=True, help="安装目录")
    parser.add_argument("--instance", default="default", help="实例名称")
    parser.add_argument("--qq", default="", help="QQ号")
    parser.add_argument("--napcat-port", type=int, default=8095, help="NapCat端口")
    parser.add_argument("--adapter-port", type=int, default=18002, help="适配器端口")
    parser.add_argument("--maibot-port", type=int, default=8000, help="MaiBot端口")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    args = parser.parse_args()
    
    # 启用调试日志
    if args.debug:
        logging.getLogger("MaiBot-Configurator").setLevel(logging.DEBUG)
        # 添加文件处理器以记录详细日志
        log_file = os.path.join(os.getcwd(), "maibot_configurator_debug.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logging.getLogger("MaiBot-Configurator").addHandler(file_handler)
        logger.info(f"调试日志将保存至: {log_file}")
    
    configurator = BotConfigurator(args.dir, args.instance)
    
    # 模拟前端传递的参数结构
    test_config_params = {
        "instance_name": args.instance, # Though configurator gets it in __init__
        "qq_number": args.qq,
        "install_napcat": True, # Example: user checked "Install NapCat"
        "install_adapter": True, # Example: user checked "Install Adapter"
        "ports": {
            "maibot": args.maibot_port,
            "adapter": args.adapter_port,
            "napcat": args.napcat_port
        },
        "model_type": "chatglm" # Example
    }
    
    result = configurator.configure(test_config_params)
    
    # 打印配置结果
    if result["success"]:
        print(f"\n✓ 成功: {result['message']}")
        print(f"- 基础目录: {result['base_dir']}")
        print(f"- MaiBot目录: {result['maibot_dir']}")
        print(f"- 适配器目录: {result['adapter_dir']}")
    else:
        print(f"\n× 失败: {result['message']}")
    
    print("\nJSON结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False)) # ensure_ascii for Chinese chars

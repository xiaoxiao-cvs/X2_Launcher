import os
import sys
import re
import json
import shutil
import logging
import random
from pathlib import Path
from typing import Dict, List, Optional, Union

# 使用 tomli/tomli_w 代替 toml
try:
    import tomli as toml_reader  # 用于读取TOML
    import tomli_w as toml_writer  # 用于写入TOML
except ImportError:
    print("错误: 缺少必要的TOML处理库")
    print("请安装所需依赖: pip install tomli tomli_w")
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
    
    def __init__(self, base_dir: str, instance_name: str = "default"):
        """初始化配置器
        
        Args:
            base_dir: 基础安装目录
            instance_name: 实例名称
        """
        self.base_dir = base_dir
        self.instance_name = instance_name
        self.maibot_dir = os.path.join(base_dir, "MaiBot")
        self.adapter_dir = os.path.join(base_dir, "MaiBot-Napcat-Adapter")
        self.config_dir = os.path.join(self.maibot_dir, "config")
        
        # 确保配置目录存在
        os.makedirs(self.config_dir, exist_ok=True)
    
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
            env_template_path = os.path.join(self.maibot_dir, "template", "template.env")
            env_path = os.path.join(self.maibot_dir, ".env")
            
            if os.path.exists(env_template_path):
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
                logger.error("模板.env文件不存在")
                return False
            
            # 2. 配置bot_config.toml
            config_template_path = os.path.join(self.maibot_dir, "template", "bot_config_template.toml")
            config_path = os.path.join(self.config_dir, "bot_config.toml")
            
            if os.path.exists(config_template_path):
                with open(config_template_path, "r", encoding="utf-8") as f:
                    config_content = f.read()
                
                # 添加模型配置
                if model_type == "chatglm":
                    config_content = self._add_chatglm_config(config_content)
                
                with open(config_path, "w", encoding="utf-8") as f:
                    f.write(config_content)
                logger.info("已配置MaiBot bot_config.toml文件")
            else:
                logger.error("模板bot_config_template.toml文件不存在")
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
                         napcat_port: int = 8095, 
                         adapter_port: int = 18002, 
                         maibot_port: int = 8000) -> bool:
        """配置MaiBot-Napcat-Adapter
        
        Args:
            qq_number: 机器人QQ号
            napcat_port: NapCat监听端口
            adapter_port: 适配器监听端口
            maibot_port: MaiBot监听端口
            
        Returns:
            bool: 是否配置成功
        """
        try:
            # 1. 配置config.toml文件
            adapter_template_path = os.path.join(self.adapter_dir, "template", "template_config.toml")
            adapter_config_path = os.path.join(self.adapter_dir, "config.toml")
            
            if os.path.exists(adapter_template_path):
                with open(adapter_template_path, "rb") as f:
                    adapter_config = toml_reader.load(f)
                
                # 更新配置
                adapter_config["Napcat_Server"] = {
                    "host": "localhost",
                    "port": napcat_port,
                    "heartbeat": 30
                }
                
                adapter_config["MaiBot_Server"] = {
                    "platform_name": "qq",
                    "host": "localhost",
                    "port": maibot_port
                }
                
                adapter_config["Napcat"] = {
                    "QQ": qq_number,
                    "bot_name": self.instance_name
                }
                
                # 添加适配器端口配置
                adapter_config["Adapter"] = {
                    "port": adapter_port
                }
                
                # 如果存在NoneBot配置
                if "NoneBot" in adapter_config:
                    adapter_config["NoneBot"]["port"] = adapter_port
                
                with open(adapter_config_path, "wb") as f:
                    toml_writer.dump(adapter_config, f)
                
                logger.info(f"已配置Adapter，设置QQ号为{qq_number}，NapCat端口为{napcat_port}，适配器端口为{adapter_port}")
            else:
                # 如果模板不存在，创建一个基本配置
                adapter_config = {
                    "Napcat_Server": {
                        "host": "localhost",
                        "port": napcat_port,
                        "heartbeat": 30
                    },
                    "MaiBot_Server": {
                        "platform_name": "qq",
                        "host": "localhost",
                        "port": maibot_port
                    },
                    "Napcat": {
                        "QQ": qq_number,
                        "bot_name": self.instance_name
                    },
                    "Adapter": {
                        "port": adapter_port
                    }
                }
                
                with open(adapter_config_path, "wb") as f:
                    toml_writer.dump(adapter_config, f)
                
                logger.info(f"已创建Adapter配置，设置QQ号为{qq_number}，NapCat端口为{napcat_port}，适配器端口为{adapter_port}")
            
            return True
        except Exception as e:
            logger.error(f"配置Adapter时出错：{e}")
            return False
    
    def create_napcat_config(self) -> str:
        """创建NapCat的配置说明文件
        
        Returns:
            str: 配置说明文本
        """
        napcat_config_path = os.path.join(self.base_dir, "napcat_config_guide.txt")
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
        
        return content
    
    def create_startup_scripts(self) -> bool:
        """创建启动脚本
        
        Returns:
            bool: 是否创建成功
        """
        try:
            # 1. 创建MaiBot启动脚本
            maibot_script_path = os.path.join(self.base_dir, "start_maibot.bat")
            maibot_script = f"""@echo off
echo 正在启动MaiBot...
cd {self.maibot_dir}
call {os.path.join(self.maibot_dir, "venv", "Scripts", "activate.bat")}
python bot.py
pause
"""
            with open(maibot_script_path, "w", encoding="utf-8") as f:
                f.write(maibot_script)
            logger.info(f"已创建MaiBot启动脚本：{maibot_script_path}")
            
            # 2. 创建Adapter启动脚本
            adapter_script_path = os.path.join(self.base_dir, "start_adapter.bat")
            adapter_script = f"""@echo off
echo 正在启动MaiBot-Napcat-Adapter...
cd {self.adapter_dir}
call {os.path.join(self.maibot_dir, "venv", "Scripts", "activate.bat")}
python main.py
pause
"""
            with open(adapter_script_path, "w", encoding="utf-8") as f:
                f.write(adapter_script)
            logger.info(f"已创建Adapter启动脚本：{adapter_script_path}")
            
            # 3. 创建启动顺序指南
            startup_guide_path = os.path.join(self.base_dir, "启动说明.txt")
            startup_guide = """# MaiBot 启动说明

请按以下顺序启动各组件：

1. 首先启动 NapCat（请参考"napcat_config_guide.txt"进行配置）
2. 运行 start_adapter.bat 启动 MaiBot-Napcat-Adapter
3. 运行 start_maibot.bat 启动 MaiBot 主程序

正确的启动顺序很重要，否则各组件之间可能无法正常通信。
"""
            with open(startup_guide_path, "w", encoding="utf-8") as f:
                f.write(startup_guide)
            logger.info(f"已创建启动说明：{startup_guide_path}")
            
            return True
        except Exception as e:
            logger.error(f"创建启动脚本时出错：{e}")
            return False
    
    def configure(self, config: dict) -> dict:
        """执行完整的配置流程
        
        Args:
            config: 配置参数
        
        Returns:
            dict: 配置结果
        """
        qq_number = config.get("qq_number", "")
        napcat_port = config.get("napcat_port", 8095)
        adapter_port = config.get("adapter_port", 18002)  # 使用适配器端口而不是nonebot_port
        maibot_port = config.get("maibot_port", 8000)
        model_type = config.get("model_type", "chatglm")
        
        logger.info(f"开始配置实例 {self.instance_name}")
        
        # 配置MaiBot
        maibot_configured = self.configure_maibot(
            maibot_port=maibot_port,
            model_type=model_type
        )
        if not maibot_configured:
            return {
                "success": False,
                "message": "配置MaiBot失败"
            }
        
        # 配置Adapter
        adapter_configured = self.configure_adapter(
            qq_number=qq_number,
            napcat_port=napcat_port,
            adapter_port=adapter_port,  # 传递适配器端口
            maibot_port=maibot_port
        )
        if not adapter_configured:
            return {
                "success": False,
                "message": "配置Adapter失败"
            }
        
        # 创建NapCat配置指南
        self.create_napcat_config()
        
        # 创建启动脚本
        scripts_created = self.create_startup_scripts()
        if not scripts_created:
            return {
                "success": False,
                "message": "创建启动脚本失败，但配置已完成"
            }
        
        # 返回配置结果
        return {
            "success": True,
            "message": "配置成功完成",
            "base_dir": self.base_dir,
            "maibot_dir": self.maibot_dir,
            "adapter_dir": self.adapter_dir,
            "config": {
                "qq_number": qq_number,
                "napcat_port": napcat_port,
                "adapter_port": adapter_port,
                "maibot_port": maibot_port,
                "model_type": model_type
            },
            "startup_files": {
                "maibot": os.path.join(self.base_dir, "start_maibot.bat"),
                "adapter": os.path.join(self.base_dir, "start_adapter.bat"),
                "guide": os.path.join(self.base_dir, "启动说明.txt"),
                "napcat_config": os.path.join(self.base_dir, "napcat_config_guide.txt")
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
    args = parser.parse_args()
    
    configurator = BotConfigurator(args.dir, args.instance)
    result = configurator.configure({
        "qq_number": args.qq,
        "napcat_port": args.napcat_port,
        "adapter_port": args.adapter_port,
        "maibot_port": args.maibot_port
    })
    print(json.dumps(result, indent=2))

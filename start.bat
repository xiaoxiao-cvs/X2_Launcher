@echo off
echo 正在启动 X2 Launcher...

:: 确保当前目录是项目根目录
cd /d %~dp0

:: 检查 Python 虚拟环境是否存在
if exist .venv\Scripts\activate.bat (
    echo 激活虚拟环境...
    call .venv\Scripts\activate.bat
) else (
    echo 虚拟环境不存在，创建新的虚拟环境...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo 安装后端依赖...
    pip install -r requirements.txt
)

:: 检查前端依赖
cd frontend
if not exist node_modules (
    echo 安装前端依赖...
    npm install
)

:: 启动应用
echo 启动应用...
npm run dev:all

:: 结束时自动关闭
pause

@echo off
echo ===== X2 Launcher 依赖安装脚本 =====
echo.

REM 检查Python虚拟环境是否存在
if not exist ".venv\Scripts\python.exe" (
    echo 正在创建Python虚拟环境...
    python -m venv .venv
    if %ERRORLEVEL% NEQ 0 (
        echo 创建虚拟环境失败，请确保已安装Python 3.9+
        pause
        exit /b 1
    )
)

echo 激活虚拟环境...
call .venv\Scripts\activate.bat

echo 更新pip...
python -m pip install --upgrade pip -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple

echo 开始安装必要的依赖...
pip install fastapi uvicorn websockets python-multipart aiohttp psutil packaging tomli tomli_w requests pydantic -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple

echo 安装可选的依赖...
pip install pillow -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple

echo.
echo 依赖安装完成！
echo.
echo 现在可以启动应用了: npm run dev
pause

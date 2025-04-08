@echo off

chcp 65001

REM 保存当前目录
set "CURRENT_DIR=%CD%"

REM 查找所有 Python 版本
echo 正在查找 Python 版本...
for /f "tokens=*" %%i in ('where python') do (
    echo 检查 Python 路径: %%i
    "%%i" -c "import sys; exit(0) if sys.version_info[0] == 3 and 9 <= sys.version_info[1] <= 12 else exit(1)" && (
        set "PYTHON_PATH=%%i"
        goto :found_python
    )
)

echo 未找到符合要求的 Python 版本（3.9-3.12），将尝试自动安装 Python 3.12.8...

REM 下载Python 3.12.8安装包
powershell -Command "(New-Object System.Net.WebClient).DownloadFile('https://mirrors.aliyun.com/python-release/windows/python-3.12.8-amd64.exe', 'python-3.12.8-amd64.exe')"
if not exist "python-3.12.8-amd64.exe" (
    echo 下载Python安装包失败
    pause
    exit /b 1
)

REM 静默安装Python
echo 正在安装Python 3.12.8...
start /wait python-3.12.8-amd64.exe /quiet InstallAllUsers=1 PrependPath=1


REM 等待环境变量更新
echo 等待系统环境变量更新...
timeout /t 5 /nobreak >nul

REM 刷新环境变量并检查Python安装
setx PATH "%PATH%" >nul
set "PATH=%PATH%"

REM 检查Python是否安装成功
where python >nul 2>&1
if %errorlevel% equ 0 (
    for /f "delims=" %%i in ('where python') do (
        echo 检查新安装的Python: %%i
        "%%i" -c "import sys; exit(0) if sys.version_info[0] == 3 and 9 <= sys.version_info[1] <= 12 else exit(1)" && (
            set "PYTHON_PATH=%%i"
            goto :found_python
        )
    )
)

echo Python安装失败，请手动安装Python 3.12.8（也有可能是已经装好了但是程序没有检测到，请重启脚本）
pause
exit /b 1

:found_python
echo 找到符合要求的 Python: %PYTHON_PATH%

REM 检查虚拟环境是否存在且可用
if exist "venv" (
    echo 检测到现有虚拟环境，正在检查是否可用...
    call venv\Scripts\activate.bat
    python -c "import sys; exit(0) if sys.version_info[0] == 3 and 9 <= sys.version_info[1] <= 12 else exit(1)" && (
        echo 虚拟环境可用
        goto :install_deps
    )
    echo 虚拟环境不可用，将创建新的虚拟环境
    rmdir /s /q venv
)

echo 正在创建虚拟环境...
"%PYTHON_PATH%" -m venv venv
call venv\Scripts\activate.bat

:install_deps
REM 更新 pip
echo 正在更新 pip...
python -m pip install -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple --upgrade pip

REM 安装依赖
echo 正在安装依赖...
pip install -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple -r requirements.txt

REM 进入maim_message目录安装本地包
cd dependents\maim_message
echo 正在安装maim_message本地包...
pip install -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple -e .

REM 返回原目录
cd ..\..

REM 安装nb-cli
echo 正在安装nb-cli...
pip install -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple nonebot2[fastapi] nonebot-adapter-onebot nb-cli
REM 调用init_napcat.py更新配置
cls
python init_napcat.py

echo 安装完成！请运行启动脚本！

pause
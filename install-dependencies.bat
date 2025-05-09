@echo off
chcp 65001 > nul
echo ===================================================
echo X2 Launcher 一键安装依赖项脚本
echo ===================================================
echo.

echo 正在检查必要的工具...
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未找到 Node.js，请先安装 Node.js（https://nodejs.org）
    goto :error
)

where python >nul 2>nul || where python3 >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.8 或更高版本（https://www.python.org）
    goto :error
)

echo.
echo 步骤1: 正在安装前端依赖项...
cd "%~dp0frontend"
if not exist node_modules (
    echo 首次安装前端依赖项，这可能需要几分钟...
    call npm install
    if %errorlevel% neq 0 goto :frontend_error
) else (
    echo 更新前端依赖项...
    call npm update
    if %errorlevel% neq 0 goto :frontend_error
)

echo.
echo 前端依赖项安装成功！
echo.

echo 步骤2: 正在安装后端依赖项...
cd "%~dp0backend"
if exist requirements.txt (
    echo 检测到 requirements.txt 文件
    python -m pip install -U pip
    python -m pip install -r requirements.txt
    if %errorlevel% neq 0 goto :backend_error
) else (
    echo [警告] 未找到 requirements.txt 文件，无法安装后端依赖项
)

echo.
echo ===================================================
echo 所有依赖项安装完成！
echo.
echo 您现在可以通过以下命令启动开发服务器：
echo   - 前端: cd frontend && npm run dev
echo   - 后端: cd backend && python main.py
echo ===================================================
goto :end

:frontend_error
echo.
echo [错误] 安装前端依赖项时出错
goto :error

:backend_error
echo.
echo [错误] 安装后端依赖项时出错
goto :error

:error
echo.
echo 安装过程中遇到错误，请查看上方错误信息
echo 如需帮助，请访问项目 GitHub 页面或提交 Issue
pause
exit /b 1

:end
echo.
echo 按任意键退出...
pause > nul
exit /b 0

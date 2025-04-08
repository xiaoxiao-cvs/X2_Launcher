const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

function logMessage(message) {
    console.log(`[Cleanup] ${message}`);
}

function cleanup() {
    try {
        if (process.platform === 'win32') {
            // 创建一个临时脚本来识别并杀死特定的Python进程
            const scriptPath = path.join(__dirname, 'temp_kill.ps1');
            const lockFilePath = path.join(__dirname, '..', '.lock');
            
            // 采用PowerShell脚本获取进程详细信息并针对性清理
            const psScript = `
            # 获取所有Python进程并检查命令行参数
            Get-WmiObject Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe'" | 
            Where-Object { $_.CommandLine -like '*X2_Launcher*' -or $_.CommandLine -like '*main.py*' } |
            ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

            # 获取所有Node进程并检查命令行参数
            Get-WmiObject Win32_Process -Filter "Name='node.exe'" | 
            Where-Object { $_.CommandLine -like '*X2_Launcher*electron*' } | 
            ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

            # 如果存在锁文件，清除它
            if (Test-Path "${lockFilePath}") {
                Remove-Item "${lockFilePath}" -Force
            }
            `;
            
            fs.writeFileSync(scriptPath, psScript);
            
            try {
                execSync(`powershell -ExecutionPolicy Bypass -File "${scriptPath}"`, { stdio: 'ignore' });
            } finally {
                // 清理临时脚本
                if (fs.existsSync(scriptPath)) {
                    fs.unlinkSync(scriptPath);
                }
            }
            
            // 清理可能的临时文件
            const tempFiles = ['.pytest_cache', '__pycache__', '*.pyc'];
            tempFiles.forEach(pattern => {
                try {
                    execSync(`del /F /Q /S "${pattern}" 2>nul`, { stdio: 'ignore' });
                } catch (e) {}
            });
        } else {
            // Linux/Mac系统使用更精确的pkill命令
            execSync('pkill -f "python.*X2_Launcher/main.py" || true');
            execSync('pkill -f "node.*X2_Launcher.*electron" || true');
        }
        logMessage('进程清理完成');
    } catch (error) {
        logMessage(`清理过程出错: ${error.message}`);
    }
}

// 执行清理
cleanup();

// 确保脚本完成后退出
setTimeout(() => {
    process.exit(0);
}, 1000);

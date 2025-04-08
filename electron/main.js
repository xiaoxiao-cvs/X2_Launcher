const { app, BrowserWindow, Tray, Menu, nativeImage, ipcMain } = require('electron')
const { PythonShell } = require('python-shell')
const path = require('path')
const { spawn } = require('child_process')
const fs = require('fs')

// 环境配置
process.env.ELECTRON_DISABLE_SECURITY_WARNINGS = true;
process.traceDeprecation = true;
process.env.ELECTRON_ENABLE_LOGGING = true

let mainWindow
let pythonProcess
let tray
let cleanupComplete = false;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1280,
        height: 720,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            nodeIntegration: false,
            contextIsolation: true,
            sandbox: true
        },
        autoHideMenuBar: true,
        icon: path.join(__dirname, '../assets/app.ico'),
        show: false
    })

    if (process.env.NODE_ENV === 'development') {
        mainWindow.loadURL('http://localhost:3000')
        mainWindow.webContents.openDevTools()
    } else {
        mainWindow.loadFile(path.join(__dirname, '../frontend/dist/index.html'))
    }

    mainWindow.once('ready-to-show', () => {
        mainWindow.show()
    })

    mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDesc) => {
        console.error('窗口加载失败:', errorCode, errorDesc)
        loadFallbackPage()
    })
}

function loadFallbackPage() {
    const indexPath = path.join(__dirname, '../frontend/dist/index.html')
    if (fs.existsSync(indexPath)) {
        mainWindow.loadFile(indexPath)
            .catch(err => {
                console.error('加载本地文件失败:', err)
                showErrorPage()
            })
    } else {
        showErrorPage()
    }
}

function showErrorPage() {
    mainWindow.loadURL(`data:text/html;charset=utf-8,
        <html><body style="padding:20px;font-family:sans-serif">
        <h2>应用加载失败</h2>
        <p>请检查以下问题：</p>
        <ul>
            <li>确保前端已构建（运行npm run build）</li>
            <li>检查控制台日志</li>
            <li>重启应用</li>
        </ul>
        </body></html>`)
}

// 启动Python后端
function startPythonBackend() {
    if (pythonProcess) {
        console.log('Python backend is already running')
        return
    }

    try {
        const pythonPath = path.join(__dirname, '../.venv/Scripts/python.exe')
        const mainPath = path.join(__dirname, '../main.py')

        // 检查 Python 和主文件是否存在
        if (!fs.existsSync(pythonPath)) {
            console.error(`Python 路径不存在: ${pythonPath}`)
            return
        }

        if (!fs.existsSync(mainPath)) {
            console.error(`主文件不存在: ${mainPath}`)
            return
        }

        console.log(`启动后端: ${pythonPath} ${mainPath}`)

        pythonProcess = spawn(pythonPath, [mainPath], {
            cwd: path.join(__dirname, '..'),
            env: { ...process.env, PYTHONUNBUFFERED: '1' },
            windowsHide: false // 尝试在Windows上保持窗口可见
        })

        console.log(`后端进程已启动，PID: ${pythonProcess.pid}`)

        pythonProcess.stdout.on('data', (data) => {
            console.log(`Backend: ${data}`)
        })

        pythonProcess.stderr.on('data', (data) => {
            console.error(`Backend Error: ${data}`)
        })

        pythonProcess.on('exit', (code) => {
            console.log(`Backend process exited with code ${code}`)
            pythonProcess = null  // 重置进程引用

            if (code !== 0 && !app.isQuitting) {
                // 可以尝试重启
                // setTimeout(startPythonBackend, 3000)
            }
        })

        // 添加错误处理
        pythonProcess.on('error', (err) => {
            console.error(`Failed to start backend process: ${err}`)
            pythonProcess = null
        })
    } catch (error) {
        console.error(`启动后端错误: ${error}`)
        pythonProcess = null
    }
}

function createTray() {
    try {
        const iconPath = path.join(__dirname, '../assets/app.ico')
        let trayIcon
        
        if (!fs.existsSync(iconPath)) {
            console.warn('使用默认图标')
            trayIcon = nativeImage.createFromPath(path.join(__dirname, '../assets/default.png'))
        } else {
            trayIcon = nativeImage.createFromPath(iconPath)
        }

        // 确保图标不为空
        if (trayIcon.isEmpty()) {
            trayIcon = nativeImage.createEmpty()
        }

        tray = new Tray(trayIcon)
        tray.setToolTip('X² Launcher')

        const contextMenu = Menu.buildFromTemplate([
            { label: '显示主窗口', click: () => mainWindow.show() },
            { type: 'separator' },
            { label: '退出', click: () => {
                cleanup()
                app.quit()
            }}
        ])
        tray.setContextMenu(contextMenu)
        tray.on('click', () => mainWindow.show())
    } catch (error) {
        console.error('托盘创建失败:', error)
    }
}

function cleanup() {
    if (cleanupComplete) return
    cleanupComplete = true

    if (pythonProcess) {
        pythonProcess.kill()
        pythonProcess = null
    }
}

function setupIPCHandlers() {
    // 系统性能监控
    ipcMain.handle('get-system-metrics', async () => {
        return new Promise((resolve) => {
            // 添加超时处理
            const timeout = setTimeout(() => {
                console.error('获取系统指标超时');
                resolve({
                    error: true,
                    message: '操作超时'
                });
            }, 5000);  // 5秒超时

            try {
                // 获取正确的Python路径
                let pythonPath = 'python';  // 默认路径
                if (process.env.PYTHON_PATH) {
                    pythonPath = process.env.PYTHON_PATH;
                } else if (fs.existsSync(path.join(__dirname, '../.venv/Scripts/python.exe'))) {
                    pythonPath = path.join(__dirname, '../.venv/Scripts/python.exe');
                }

                // 检查脚本路径是否存在
                const scriptPath = path.join(__dirname, '../src/utils/system_monitor.py');
                if (!fs.existsSync(scriptPath)) {
                    clearTimeout(timeout);
                    console.error(`系统监控脚本不存在: ${scriptPath}`);
                    return resolve({
                        error: true,
                        message: '监控脚本不存在'
                    });
                }

                console.log(`使用Python路径: ${pythonPath}`);
                
                // 直接使用子进程执行Python脚本以避免PythonShell可能的问题
                const childProcess = spawn(pythonPath, [scriptPath], {
                    cwd: path.dirname(scriptPath),
                    env: { ...process.env }
                });

                let stdoutData = '';
                let stderrData = '';

                childProcess.stdout.on('data', (data) => {
                    stdoutData += data.toString();
                });

                childProcess.stderr.on('data', (data) => {
                    stderrData += data.toString();
                    console.error(`系统监控错误: ${data}`);
                });

                childProcess.on('error', (err) => {
                    clearTimeout(timeout);
                    console.error('Python执行错误:', err);
                    resolve({
                        error: true,
                        message: err.message || '执行出错'
                    });
                });

                childProcess.on('close', (code) => {
                    clearTimeout(timeout);
                    
                    if (code !== 0) {
                        console.error(`系统监控脚本异常退出: ${code}`);
                        return resolve({
                            error: true,
                            message: `脚本退出代码: ${code}`
                        });
                    }

                    try {
                        // 尝试解析JSON输出
                        const result = JSON.parse(stdoutData.trim());
                        console.log('成功获取系统指标');
                        resolve(result);
                    } catch (err) {
                        console.error('解析系统指标失败:', err, 'Raw output:', stdoutData);
                        resolve({
                            error: true,
                            message: '解析系统数据失败'
                        });
                    }
                });
            } catch (err) {
                clearTimeout(timeout);
                console.error('执行系统监控脚本失败:', err);
                resolve({
                    error: true,
                    message: err.message || '初始化失败'
                });
            }
        });
    });
}

// 添加清理事件监听
process.on('SIGINT', () => {
    cleanup();
    app.quit();
});

process.on('SIGTERM', () => {
    cleanup();
    app.quit();
});

app.on('before-quit', () => {
    cleanup();
});

app.whenReady().then(() => {
    createWindow()
    startPythonBackend()
    setupIPCHandlers()
})

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit()
    }
})

app.on('will-quit', () => {
    if (pythonProcess) {
        pythonProcess.kill()
    }
})

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow()
    }
})

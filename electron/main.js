const { app, BrowserWindow, Tray, Menu } = require('electron')
const path = require('path')
const { spawn } = require('child_process')

let mainWindow
let pythonProcess
let tray

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1280,
        height: 720,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            sandbox: true,
            preload: path.join(__dirname, 'preload.js')
        },
        autoHideMenuBar: true,
        icon: path.join(__dirname, '../assets/app.ico')
    })

    // 启动Python后端
    startPythonBackend()

    // 加载应用
    loadApplication()

    createTray()
}

function startPythonBackend() {
    const pythonPath = path.join(__dirname, '../.venv/Scripts/python.exe')
    pythonProcess = spawn(pythonPath, ['main.py'], {
        cwd: path.join(__dirname, '..')
    })

    pythonProcess.stdout.on('data', (data) => {
        console.log(`Backend: ${data}`)
    })

    pythonProcess.stderr.on('data', (data) => {
        console.error(`Backend Error: ${data}`)
    })
}

async function loadApplication() {
    try {
        if (process.env.NODE_ENV === 'development') {
            // 先尝试连接开发服务器
            await mainWindow.loadURL('http://localhost:3000')
            mainWindow.webContents.openDevTools()
        } else {
            // 先尝试连接Python后端
            await mainWindow.loadURL('http://localhost:8000')
                .catch(async () => {
                    // 如果失败则加载本地文件
                    await mainWindow.loadFile(path.join(__dirname, '../frontend/dist/index.html'))
                })
        }
    } catch (err) {
        console.error('应用加载失败:', err)
    }
}

function createTray() {
    tray = new Tray(path.join(__dirname, '../assets/app.ico'))
    tray.setToolTip('X² Launcher')
    
    const contextMenu = Menu.buildFromTemplate([
        { label: '显示', click: () => mainWindow.show() },
        { label: '退出', click: () => {
            app.isQuitting = true
            app.quit()
        }}
    ])
    
    tray.setContextMenu(contextMenu)
    tray.on('click', () => mainWindow.show())
}

app.whenReady().then(createWindow)

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

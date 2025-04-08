const { app, BrowserWindow } = require('electron')
const path = require('path')
const { spawn } = require('child_process')
require('@electron/remote/main').initialize()

let mainWindow
let pythonProcess

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1280,
        height: 720,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: true,
            enableRemoteModule: true,
            preload: path.join(__dirname, 'electron/preload.js')
        }
    })

    // 启动Python后端服务
    startPythonBackend()

    // 根据环境加载页面
    if (process.env.NODE_ENV === 'development') {
        mainWindow.loadURL('http://localhost:3000')
        mainWindow.webContents.openDevTools()
    } else {
        mainWindow.loadFile(path.join(__dirname, 'frontend/dist/index.html'))
    }
}

function startPythonBackend() {
    // 使用python虚拟环境启动后端
    const pythonPath = path.join(__dirname, '.venv/Scripts/python.exe')
    pythonProcess = spawn(pythonPath, ['src/main.py'])
    
    pythonProcess.stdout.on('data', (data) => {
        console.log(`Backend: ${data}`)
    })

    pythonProcess.stderr.on('data', (data) => {
        console.error(`Backend Error: ${data}`)
    })
}

app.whenReady().then(createWindow)

app.on('window-all-closed', () => {
    if (pythonProcess) {
        pythonProcess.kill()
    }
    if (process.platform !== 'darwin') {
        app.quit()
    }
})

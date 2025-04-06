const { app, BrowserWindow } = require('electron')
const path = require('path')
const { spawn } = require('child_process')

let mainWindow
let pythonProcess

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        }
    })

    // 启动后端服务
    startPythonBackend()

    // 加载前端页面
    mainWindow.loadURL('http://localhost:3000')
}

function startPythonBackend() {
    // 启动打包后的后端程序
    const backendPath = path.join(__dirname, 'backend', 'main.exe')
    pythonProcess = spawn(backendPath)

    pythonProcess.stdout.on('data', (data) => {
        console.log(`Backend: ${data}`)
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

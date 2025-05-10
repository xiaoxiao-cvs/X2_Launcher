const { app, BrowserWindow } = require("electron");
const path = require("path");
const { spawn } = require("child_process");
require("@electron/remote/main").initialize();

let mainWindow;
let pythonProcess;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 720,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: true,
      preload: path.join(__dirname, "electron/preload.js"),
    },
    autoHideMenuBar: true, // 自动隐藏菜单栏
    menuBarVisible: false, // 设置菜单栏不可见
  });

  // 设置 CSP 头
  mainWindow.webContents.session.webRequest.onHeadersReceived(
    (details, callback) => {
      callback({
        responseHeaders: {
          ...details.responseHeaders,
          "Content-Security-Policy": [
            "default-src 'self'; " +
              "script-src 'self'; " +
              "style-src 'self' 'unsafe-inline'; " +
              "img-src 'self' data:; " +
              "font-src 'self'; " +
              "connect-src 'self' http://localhost:* ws://localhost:*; " +
              "frame-src 'none';",
          ],
        },
      });
    }
  );

  // 启动Python后端服务
  startPythonBackend();

  // 根据环境加载页面
  if (process.env.NODE_ENV === "development") {
    mainWindow.loadURL("http://localhost:3000");
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, "frontend/dist/index.html"));
  }

  // 移除菜单栏
  mainWindow.setMenu(null);
}

function startPythonBackend() {
  // 使用python虚拟环境启动后端
  const pythonPath = path.join(__dirname, ".venv/Scripts/python.exe");
  pythonProcess = spawn(pythonPath, ["src/main.py"]);

  pythonProcess.stdout.on("data", (data) => {
    console.log(`Backend: ${data}`);
  });

  pythonProcess.stderr.on("data", (data) => {
    console.error(`Backend Error: ${data}`);
  });
}

app.whenReady().then(createWindow);

app.on("window-all-closed", () => {
  if (pythonProcess) {
    pythonProcess.kill();
  }
  if (process.platform !== "darwin") {
    app.quit();
  }
});

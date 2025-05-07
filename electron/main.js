const { app, BrowserWindow, ipcMain, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const os = require('os');
const fs = require('fs');

// 全局变量保存窗口引用
let mainWindow;
let backendProcess;
let pythonPath;

// 查找Python路径
function findPythonPath() {
  // 优先使用虚拟环境中的Python
  const venvPath = path.join(__dirname, '..', '.venv');
  const isWin = process.platform === 'win32';
  
  // 构建Python可执行文件路径
  const pythonExe = isWin ? 'python.exe' : 'python';
  const possiblePaths = [
    path.join(venvPath, 'Scripts', pythonExe), // Windows的虚拟环境
    path.join(venvPath, 'bin', pythonExe),     // Unix的虚拟环境
    'python',                                   // 系统Python (依赖PATH)
    'python3'                                   // 系统Python3 (依赖PATH)
  ];
  
  // 尝试找到可用的Python解释器
  for (const possiblePath of possiblePaths) {
    try {
      if (possiblePath.includes(path.sep)) {
        if (fs.existsSync(possiblePath)) {
          console.log(`找到Python路径: ${possiblePath}`);
          return possiblePath;
        }
      } else {
        // 对于系统路径中的Python，通过尝试执行来测试
        const result = spawn(possiblePath, ['--version']);
        if (result.pid) {
          console.log(`找到Python命令: ${possiblePath}`);
          return possiblePath;
        }
      }
    } catch (e) {
      // 忽略错误，继续尝试下一个路径
      console.log(`Python路径检查失败: ${possiblePath}`, e);
    }
  }
  
  console.log('未找到Python路径，使用默认值');
  return possiblePaths[0]; // 如果都失败，返回第一个备选路径
}

// 启动后端服务
function startBackend() {
  pythonPath = pythonPath || findPythonPath();
  
  // 诊断模式，如果指定了--diagnose参数
  const isDiagnostic = process.argv.includes('--diagnose');
  const scriptPath = path.join(__dirname, '..', 'backend', isDiagnostic ? 'diagnostic.py' : 'main.py');
  
  console.log(`启动后端: ${pythonPath} ${scriptPath}`);
  
  // 设置环境变量以确保UTF-8编码
  const env = Object.assign({}, process.env, { 
    PYTHONIOENCODING: 'utf-8',
    PYTHONLEGACYWINDOWSSTDIO: 'utf-8'
  });
  
  backendProcess = spawn(pythonPath, [scriptPath], {
    env: env,
    stdio: 'pipe', // 捕获标准输出和错误
    cwd: path.join(__dirname, '..', 'backend') // 设置工作目录
  });
  
  console.log(`后端进程已启动，PID: ${backendProcess.pid}`);
  
  // 处理后端输出
  backendProcess.stdout.on('data', (data) => {
    const output = data.toString();
    console.log(`Backend: ${output}`);
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('backend-output', output);
    }
  });
  
  // 处理后端错误
  backendProcess.stderr.on('data', (data) => {
    const error = data.toString();
    console.error(`Backend Error: ${error}`);
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('backend-error', error);
    }
  });
  
  // 处理后端退出
  backendProcess.on('exit', (code, signal) => {
    console.log(`Backend process exited with code ${code}`);
    
    // 如果不是诊断模式且后端异常退出，尝试启动诊断
    if (!isDiagnostic && code !== 0) {
      console.log('后端异常退出，启动诊断...');
      setTimeout(() => {
        startDiagnostic();
      }, 1000);
    }
    
    backendProcess = null;
  });
  
  // 错误处理
  backendProcess.on('error', (err) => {
    console.error(`Failed to start backend process: ${err}`);
  });
}

// 启动诊断
function startDiagnostic() {
  pythonPath = pythonPath || findPythonPath();
  const diagnosticPath = path.join(__dirname, '..', 'backend', 'diagnostic.py');
  
  console.log(`启动诊断: ${pythonPath} ${diagnosticPath}`);
  
  const diagnosticProcess = spawn(pythonPath, [diagnosticPath], {
    env: Object.assign({}, process.env, { 
      PYTHONIOENCODING: 'utf-8',
      PYTHONLEGACYWINDOWSSTDIO: 'utf-8'
    }),
    stdio: 'pipe',
    cwd: path.join(__dirname, '..', 'backend')
  });
  
  diagnosticProcess.stdout.on('data', (data) => {
    console.log(`Diagnostic: ${data.toString()}`);
  });
  
  diagnosticProcess.stderr.on('data', (data) => {
    console.error(`Diagnostic Error: ${data.toString()}`);
  });
}

// 创建主窗口
function createWindow() {
  // 创建浏览器窗口
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    icon: path.join(__dirname, '..', 'frontend', 'public', 'assets', 'icon.ico'), // 添加图标路径
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    title: 'X² Launcher',
    backgroundColor: '#1a2a42',
    autoHideMenuBar: true, // 自动隐藏菜单栏
    menuBarVisible: false, // 设置菜单栏不可见
  });

  // 开发模式直接连接Vite服务器
  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:3000');
    mainWindow.webContents.openDevTools(); // 自动打开开发工具
  } else {
    // 生产模式加载打包后的文件
    mainWindow.loadFile(path.join(__dirname, '..', 'frontend', 'dist', 'index.html'));
  }

  // 移除菜单栏
  mainWindow.setMenu(null);

  // 窗口关闭处理
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// 应用初始化完成时创建窗口
app.whenReady().then(() => {
  console.log('Starting Electron...');
  // 设置为开发模式
  process.env.NODE_ENV = 'development';
  
  // 启动后端
  startBackend();
  
  // 创建窗口
  createWindow();
  
  // macOS特殊处理
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
  
  // 设置IPC处理程序
  setupIPC();
});

// 应用退出前关闭后端
app.on('before-quit', () => {
  if (backendProcess) {
    // 在Windows上需要强制杀死，否则会留下孤儿进程
    if (process.platform === 'win32') {
      try {
        require('child_process').execSync(`taskkill /pid ${backendProcess.pid} /T /F`);
      } catch (e) {
        console.error(`Failed to kill backend process: ${e}`);
      }
    } else {
      backendProcess.kill('SIGTERM');
    }
  }
});

// 所有窗口关闭时退出应用
app.on('window-all-closed', () => {
  // macOS特殊处理
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// 设置IPC通信
function setupIPC() {
  // 处理性能数据请求
  ipcMain.handle('get-system-metrics', async () => {
    try {
      // 这里应该使用适当的方法获取系统性能数据
      // 可以调用系统API或通过后端获取
      const metrics = {
        cpu: { 
          usage: Math.random() * 30 + 20,
          percent: Math.random() * 30 + 20,
          cores: os.cpus().length,
          frequency: os.cpus()[0].speed
        },
        memory: {
          total: os.totalmem(),
          free: os.freemem(),
          used: os.totalmem() - os.freemem(),
          percent: ((os.totalmem() - os.freemem()) / os.totalmem()) * 100
        },
        network: {
          // 这里需要更好的实现来获取网络数据
          sent: Math.random() * 5000 * 1024,
          received: Math.random() * 8000 * 1024,
          sentRate: Math.random() * 300 * 1024,
          receivedRate: Math.random() * 500 * 1024
        }
      };
      return metrics;
    } catch (error) {
      console.error('获取系统指标失败:', error);
      return { error: true, message: error.message };
    }
  });
  
  // 处理打开文件夹请求
  ipcMain.on('open-folder', (event, folderPath) => {
    if (folderPath) {
      shell.openPath(folderPath).catch(err => {
        console.error(`Failed to open folder ${folderPath}: ${err}`);
      });
    }
  });
}

/**
 * 预加载脚本 - 在渲染进程加载前执行
 * 用于提供 Electron API 的安全访问
 */
const { contextBridge, ipcRenderer } = require('electron');

// 暴露受控的 API 给渲染进程
contextBridge.exposeInMainWorld('electronAPI', {
  // 获取系统指标
  getSystemMetrics: async () => {
    try {
      // 尝试通过IPC调用主进程获取系统指标
      return await ipcRenderer.invoke('get-system-metrics');
    } catch (error) {
      console.error('获取系统指标失败:', error);
      // 提供模拟数据作为后备
      return {
        cpu: { 
          usage: Math.random() * 30 + 20,
          cores: 8,
          frequency: 2400 
        },
        memory: {
          total: 16 * 1024 * 1024 * 1024,
          used: (Math.random() * 4 + 6) * 1024 * 1024 * 1024,
          free: 6 * 1024 * 1024 * 1024
        },
        network: {
          sent: Math.random() * 5000 * 1024,
          received: Math.random() * 8000 * 1024,
          sentRate: Math.random() * 300 * 1024,
          receivedRate: Math.random() * 500 * 1024
        }
      };
    }
  },
  
  // 打开文件夹
  openFolder: (path) => ipcRenderer.send('open-folder', path),

  // 监听应用事件
  onAppEvent: (event, callback) => {
    ipcRenderer.on(event, (_, ...args) => callback(...args));
    // 返回一个清理函数
    return () => {
      ipcRenderer.removeAllListeners(event);
    };
  }
});

// 添加后端日志监听器
ipcRenderer.on('backend-output', (_, message) => {
  console.log(`[Backend] ${message}`);
});

ipcRenderer.on('backend-error', (_, message) => {
  console.error(`[Backend Error] ${message}`);
});

// 通知渲染进程预加载已完成
console.log('预加载脚本已执行');

// 预加载脚本，可用于在渲染进程中提供 Node.js API
window.addEventListener('DOMContentLoaded', () => {
  const replaceText = (selector, text) => {
    const element = document.getElementById(selector);
    if (element) element.innerText = text;
  };

  for (const dependency of ['chrome', 'node', 'electron']) {
    replaceText(`${dependency}-version`, process.versions[dependency]);
  }
});
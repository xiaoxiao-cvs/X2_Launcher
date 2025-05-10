// 使用 contextBridge 安全暴露 API 给渲染进程
const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("electron", {
  // 定义安全的 API
  send: (channel, data) => {
    // 白名单通道
    const validChannels = ["toMain", "instance-command" /* 其他合法通道 */];
    if (validChannels.includes(channel)) {
      ipcRenderer.send(channel, data);
    }
  },
  receive: (channel, func) => {
    const validChannels = ["fromMain", "instance-status" /* 其他合法通道 */];
    if (validChannels.includes(channel)) {
      // 删除旧的监听器以避免内存泄漏
      ipcRenderer.removeAllListeners(channel);
      // 添加新的监听器
      ipcRenderer.on(channel, (_, ...args) => func(...args));
    }
  },
});

const { contextBridge, ipcRenderer } = require('electron')

// 暴露API给渲染进程
contextBridge.exposeInMainWorld('electronAPI', {
    // Python后端调用
    callPython: (method, args) => ipcRenderer.invoke('python-call', method, args),
    
    // 后端消息监听
    onPythonMessage: (callback) => {
        ipcRenderer.on('python-message', (event, ...args) => callback(...args))
    },
    
    // 版本管理
    getVersions: () => ipcRenderer.invoke('get-versions'),
    deployVersion: (version) => ipcRenderer.invoke('deploy-version', version),
    startBot: (version) => ipcRenderer.invoke('start-bot', version),
    
    // 配置管理
    getConfig: () => ipcRenderer.invoke('get-config'),
    saveConfig: (config) => ipcRenderer.invoke('save-config', config)
})

const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electronAPI', {
    getSystemMetrics: () => ipcRenderer.invoke('get-system-metrics')
})

console.log('预加载脚本已执行')
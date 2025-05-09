/**
 * WebSocket服务
 * 统一处理WebSocket连接管理、消息处理、重连等逻辑
 */

// 获取当前WebSocket URL
const getWebSocketUrl = (path = '/api/logs/ws') => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}${path}`;
};

// 模拟模式标志 - 如果WebSocket连接失败，我们将使用模拟模式
let useMockMode = false;

export class WebSocketService {
  constructor(options = {}) {
    this.url = options.url || '/api/logs/ws';
    this.reconnectDelay = options.reconnectDelay || 3000;
    this.maxReconnectAttempts = options.maxReconnectAttempts || 5;
    this.autoReconnect = options.autoReconnect !== false;
    
    this.socket = null;
    this.reconnectCount = 0;
    this.reconnectTimer = null;
    this.events = {};
    this.connected = false;
  }

  connect() {
    if (this.socket && (this.socket.readyState === WebSocket.CONNECTING || 
                         this.socket.readyState === WebSocket.OPEN)) {
      return;
    }
    
    try {
      // 使用绝对URL或相对URL，确保WebSocket连接正确
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = this.url.startsWith('ws') ? this.url : 
                    `${protocol}//${window.location.host}${this.url}`;
      
      console.log(`正在连接WebSocket: ${wsUrl}`);
      this.socket = new WebSocket(wsUrl);
      
      this.socket.onopen = () => {
        console.log('WebSocket连接已建立');
        this.connected = true;
        this.reconnectCount = 0;
        this.emit('open');
      };
      
      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.emit('message', data);
        } catch (err) {
          this.emit('message', event.data);
        }
      };
      
      this.socket.onerror = (error) => {
        console.error('WebSocket错误:', error);
        this.emit('error', error);
      };
      
      this.socket.onclose = () => {
        console.log('WebSocket连接已关闭');
        this.connected = false;
        this.emit('close');
        
        if (this.autoReconnect && this.reconnectCount < this.maxReconnectAttempts) {
          this.reconnectTimer = setTimeout(() => {
            console.log(`尝试重新连接 (${this.reconnectCount + 1}/${this.maxReconnectAttempts})`);
            this.reconnectCount++;
            this.connect();
          }, this.reconnectDelay);
        } else if (this.reconnectCount >= this.maxReconnectAttempts) {
          console.warn('达到最大重连次数，启用模拟模式');
          this.startMockMode();
        }
      };
    } catch (error) {
      console.error('创建WebSocket连接失败:', error);
      this.emit('error', error);
      // 延迟重试
      if (this.autoReconnect) {
        this.reconnectTimer = setTimeout(() => {
          this.connect();
        }, this.reconnectDelay);
      }
    }
  }
  
  send(data) {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      console.error('WebSocket未连接，无法发送消息');
      return false;
    }
    
    try {
      const message = typeof data === 'string' ? data : JSON.stringify(data);
      this.socket.send(message);
      return true;
    } catch (error) {
      console.error('发送WebSocket消息失败:', error);
      return false;
    }
  }
  
  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
    
    this.connected = false;
  }
  
  on(event, callback) {
    if (!this.events[event]) {
      this.events[event] = [];
    }
    
    this.events[event].push(callback);
    return this;
  }
  
  off(event, callback) {
    if (!this.events[event]) {
      return this;
    }
    
    if (!callback) {
      delete this.events[event];
      return this;
    }
    
    this.events[event] = this.events[event].filter(cb => cb !== callback);
    return this;
  }
  
  emit(event, ...args) {
    if (!this.events[event]) {
      return;
    }
    
    this.events[event].forEach(callback => {
      try {
        callback(...args);
      } catch (error) {
        console.error(`执行事件回调出错 (${event}):`, error);
      }
    });
  }
  
  startMockMode() {
    try {
      window._useMockData = true;
      window.localStorage.setItem('useMockData', 'true');
      console.warn('已切换到模拟数据模式 (WebSocket连接失败)');
      
      // 每10秒发送一次模拟数据
      setInterval(() => {
        const mockData = {
          time: new Date().toISOString(),
          level: 'INFO',
          message: '这是模拟日志数据，WebSocket连接失败',
          source: 'mock'
        };
        this.emit('message', mockData);
      }, 10000);
    } catch (e) {
      // 忽略存储错误
    }
  }
  
  isConnected() {
    return this.connected;
  }
}

// 创建单例实例用于全局共享
let logWebSocketInstance = null;

/**
 * 获取日志WebSocket服务实例
 * @returns {WebSocketService} WebSocketService实例
 */
export const getLogWebSocketService = () => {
  if (!logWebSocketInstance) {
    logWebSocketInstance = new WebSocketService({
      url: getWebSocketUrl('/api/logs/ws'),
      reconnectDelay: 3000,
      maxReconnectAttempts: 3, // 减少重连尝试次数，更快进入模拟模式
      autoReconnect: true
    });
  }
  return logWebSocketInstance;
};

export default WebSocketService;

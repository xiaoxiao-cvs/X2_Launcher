/**
 * WebSocket服务
 * 统一处理WebSocket连接管理、消息处理、重连等逻辑
 */

// 获取当前WebSocket URL
const getWebSocketUrl = (path = '/api/logs/ws') => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}${path}`;
};

export class WebSocketService {
  constructor(options = {}) {
    this.url = options.url || getWebSocketUrl();
    this.reconnectDelay = options.reconnectDelay || 3000;
    this.maxReconnectAttempts = options.maxReconnectAttempts || 5;
    this.reconnectAttempts = 0;
    this.autoReconnect = options.autoReconnect !== false;
    this.listeners = {
      message: [],
      open: [],
      close: [],
      error: []
    };
    this.socket = null;
    this.isConnecting = false;
  }

  /**
   * 连接WebSocket
   * @returns {Promise} 连接成功或失败的Promise
   */
  connect() {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      return Promise.resolve();
    }

    if (this.isConnecting) {
      return new Promise((resolve, reject) => {
        const checkInterval = setInterval(() => {
          if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            clearInterval(checkInterval);
            resolve();
          } else if (!this.isConnecting) {
            clearInterval(checkInterval);
            reject(new Error('连接失败'));
          }
        }, 100);
      });
    }

    this.isConnecting = true;

    return new Promise((resolve, reject) => {
      try {
        this.socket = new WebSocket(this.url);

        this.socket.onopen = (event) => {
          console.log('WebSocket连接已建立:', this.url);
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.notifyListeners('open', event);
          resolve();
        };

        this.socket.onmessage = (event) => {
          this.notifyListeners('message', event);
        };

        this.socket.onerror = (error) => {
          console.error('WebSocket错误:', error);
          this.notifyListeners('error', error);
        };

        this.socket.onclose = (event) => {
          this.isConnecting = false;
          this.notifyListeners('close', event);
          console.log('WebSocket连接已关闭');

          if (this.autoReconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
            console.log(`尝试重连 (${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})...`);
            this.reconnectAttempts++;
            setTimeout(() => this.connect(), this.reconnectDelay);
          }

          // 如果是初始连接失败则拒绝Promise
          if (this.reconnectAttempts === 0) {
            reject(new Error('WebSocket连接关闭'));
          }
        };
      } catch (error) {
        this.isConnecting = false;
        console.error('创建WebSocket连接失败:', error);
        reject(error);
        
        if (this.autoReconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
          console.log(`尝试重连 (${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})...`);
          this.reconnectAttempts++;
          setTimeout(() => this.connect(), this.reconnectDelay);
        }
      }
    });
  }

  /**
   * 关闭WebSocket连接
   */
  disconnect() {
    if (this.socket) {
      this.autoReconnect = false;
      this.socket.close();
      this.socket = null;
    }
  }

  /**
   * 发送消息
   * @param {any} data 要发送的数据
   * @returns {Promise} 发送结果
   */
  send(data) {
    return new Promise((resolve, reject) => {
      if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
        this.connect()
          .then(() => {
            this.socket.send(typeof data === 'string' ? data : JSON.stringify(data));
            resolve();
          })
          .catch(reject);
      } else {
        try {
          this.socket.send(typeof data === 'string' ? data : JSON.stringify(data));
          resolve();
        } catch (error) {
          reject(error);
        }
      }
    });
  }

  /**
   * 添加事件监听器
   * @param {string} event 事件类型：message, open, close, error
   * @param {Function} callback 回调函数
   */
  on(event, callback) {
    if (this.listeners[event]) {
      this.listeners[event].push(callback);
    }
    return this;
  }

  /**
   * 移除事件监听器
   * @param {string} event 事件类型
   * @param {Function} callback 回调函数，如果不提供则移除该事件的所有监听器
   */
  off(event, callback) {
    if (!this.listeners[event]) return this;
    
    if (callback) {
      this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
    } else {
      this.listeners[event] = [];
    }
    return this;
  }

  /**
   * 通知所有监听器
   * @param {string} event 事件类型
   * @param {any} data 事件数据
   * @private
   */
  notifyListeners(event, data) {
    if (!this.listeners[event]) return;
    
    // 如果是message事件，尝试解析JSON
    if (event === 'message' && data.data) {
      try {
        const parsedData = JSON.parse(data.data);
        this.listeners[event].forEach(callback => callback(parsedData, data));
      } catch (e) {
        // 如果解析失败，则传递原始数据
        this.listeners[event].forEach(callback => callback(data.data, data));
      }
    } else {
      this.listeners[event].forEach(callback => callback(data));
    }
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
      maxReconnectAttempts: 10,
      autoReconnect: true
    });
  }
  return logWebSocketInstance;
};

export default WebSocketService;

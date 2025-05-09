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
    
    // 模拟消息生成器（当后端不可用时使用）
    this.mockInterval = null;
    this.useMockMessages = options.useMockMessages || false;
  }

  /**
   * 连接WebSocket
   * @returns {Promise} 连接成功或失败的Promise
   */
  connect() {
    // 如果全局设置了使用模拟数据，直接启动模拟模式
    if (window._useMockData === true) {
      console.log('WebSocket: 全局模拟数据模式已启用，启动模拟WebSocket');
      this.startMockMode();
      return Promise.resolve(); // 假装连接成功
    }
    
    // 以下是原有连接逻辑
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

        // 设置连接超时，缩短等待时间为3秒
        const connectionTimeout = setTimeout(() => {
          if (this.socket && this.socket.readyState !== WebSocket.OPEN) {
            console.warn('WebSocket连接超时，启动模拟模式');
            this.startMockMode();
            this.isConnecting = false;
            resolve(); // 解析Promise以避免阻塞UI
          }
        }, 3000);

        this.socket.onopen = (event) => {
          clearTimeout(connectionTimeout);
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
          clearTimeout(connectionTimeout);
          this.isConnecting = false;
          this.notifyListeners('close', event);
          console.log('WebSocket连接已关闭');

          // 如果已进行了多次尝试仍然失败，切换到模拟模式
          if (this.reconnectAttempts >= this.maxReconnectAttempts - 1) {
            console.warn('WebSocket重连失败多次，启动模拟模式');
            this.startMockMode();
            resolve(); // 解析Promise以避免阻塞UI
            return;
          }

          // 检查是否全局已切换到模拟模式
          if (window._useMockData === true) {
            console.log('检测到全局模拟模式已启用，WebSocket不再尝试重连');
            this.startMockMode();
            resolve();
            return;
          }

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
        
        // 启动模拟模式而不是无限尝试重连
        this.startMockMode();
        resolve(); // 解析Promise以避免阻塞UI
      }
    });
  }

  /**
   * 启动模拟消息模式
   * 当WebSocket连接不可用时，生成模拟消息
   */
  startMockMode() {
    if (this.mockInterval) return; // 避免重复启动
    
    useMockMode = true;
    console.log('WebSocket已切换到模拟消息模式');
    
    // 触发打开事件
    this.notifyListeners('open', { type: 'open', isMock: true });
    
    // 发送初始模拟消息
    this.sendMockInitMessages();
    
    // 定期发送模拟消息
    this.mockInterval = setInterval(() => {
      this.sendMockMessage();
    }, 5000);
    
    // 保存设置以便下次使用
    window._useMockData = true;
    try {
      window.localStorage.setItem('useMockData', 'true');
    } catch (e) {
      // 忽略存储错误
    }
  }
  
  /**
   * 发送初始模拟消息
   */
  sendMockInitMessages() {
    const initialMessages = [
      {
        time: this.formatTime(new Date()),
        level: 'INFO',
        source: 'system',
        message: '已启用WebSocket模拟模式 (后端服务未连接)'
      },
      {
        time: this.formatTime(new Date()),
        level: 'WARNING',
        source: 'system',
        message: '模拟数据仅用于界面预览，无法执行实际操作'
      },
      {
        time: this.formatTime(new Date()),
        level: 'INFO',
        source: 'system',
        message: '要使用完整功能，请启动后端服务 (npm run dev:backend)'
      }
    ];
    
    initialMessages.forEach(message => {
      this.notifyListeners('message', message);
    });
  }
  
  /**
   * 发送单条模拟消息
   */
  sendMockMessage() {
    const types = ['INFO', 'WARNING', 'ERROR', 'DEBUG'];
    const sources = ['system', 'maibot', 'napcat', 'nonebot'];
    
    const messages = [
      '这是一条模拟消息',
      '模拟系统运行中...',
      '模拟性能监控正常',
      '模拟网络请求已发送',
      '模拟消息响应已接收',
      '模拟日志记录中...',
      '模拟数据更新完成'
    ];
    
    const mockMessage = {
      time: this.formatTime(new Date()),
      level: types[Math.floor(Math.random() * types.length)],
      source: sources[Math.floor(Math.random() * sources.length)],
      message: messages[Math.floor(Math.random() * messages.length)]
    };
    
    this.notifyListeners('message', mockMessage);
  }
  
  /**
   * 格式化时间
   */
  formatTime(date) {
    return date.toLocaleString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit'
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
    
    // 停止模拟消息
    if (this.mockInterval) {
      clearInterval(this.mockInterval);
      this.mockInterval = null;
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
    if (event === 'message') {
      // 如果已经是一个对象（模拟消息），直接传递
      if (typeof data !== 'string' && !(data instanceof Event)) {
        this.listeners[event].forEach(callback => callback(data, { data }));
        return;
      }
      
      // 处理WebSocket消息事件
      if (data.data) {
        try {
          const parsedData = JSON.parse(data.data);
          this.listeners[event].forEach(callback => callback(parsedData, data));
        } catch (e) {
          // 如果解析失败，则传递原始数据
          this.listeners[event].forEach(callback => callback(data.data, data));
        }
      } else {
        // 直接传递数据
        this.listeners[event].forEach(callback => callback(data, { data }));
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
      maxReconnectAttempts: 3, // 减少重连尝试次数，更快进入模拟模式
      autoReconnect: true
    });
  }
  return logWebSocketInstance;
};

export default WebSocketService;

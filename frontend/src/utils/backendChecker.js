/**
 * 后端连接检查器
 * 用于检查后端服务是否可用并提供自动重试功能
 */

import { ElMessage } from 'element-plus';

// 连接检查配置
const CHECK_INTERVAL = 5000; // 检查间隔: 5秒
const MAX_RETRIES = 12; // 最大重试次数: 12次 (约1分钟)
const TIMEOUT = 2000; // 请求超时: 2秒

// 全局状态
let isChecking = false;
let retryCount = 0;
let checkTimer = null;
let onConnectedCallback = null;
let wasEverConnected = false;

/**
 * 检查后端连接
 * @param {Function} onConnected - 连接成功时的回调
 * @param {boolean} showNotifications - 是否显示通知
 * @returns {Promise<boolean>} 连接状态
 */
export const checkBackendConnection = async (onConnected = null, showNotifications = true) => {
  // 存储回调函数
  if (onConnected) {
    onConnectedCallback = onConnected;
  }
  
  // 正在检查中，不重复发起请求
  if (isChecking) return false;
  
  isChecking = true;
  let connected = false;
  
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), TIMEOUT);
    
    const response = await fetch('/api/status', {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    
    if (response.ok) {
      connected = true;
      window._useMockData = false;
      window.localStorage.setItem('useMockData', 'false');
      
      // 现在连接成功，但之前断开过，显示重新连接消息
      if (wasEverConnected && showNotifications) {
        ElMessage.success({
          message: '已重新连接至后端服务',
          duration: 3000
        });
      }
      
      // 执行连接成功回调
      if (onConnectedCallback) {
        onConnectedCallback();
      }
      
      // 重置重试计数
      retryCount = 0;
      wasEverConnected = true;
    } else {
      connected = false;
      enableMockMode('后端服务返回错误状态码: ' + response.status);
    }
  } catch (error) {
    connected = false;
    enableMockMode(error.name === 'AbortError' ? '连接超时' : error.message);
  } finally {
    isChecking = false;
  }
  
  return connected;
};

/**
 * 启用模拟数据模式
 * @param {string} reason - 原因描述
 */
const enableMockMode = (reason) => {
  // 如果已经在模拟模式，不重复显示消息
  if (window._useMockData === true) return;
  
  window._useMockData = true;
  window.localStorage.setItem('useMockData', 'true');
  console.warn(`已切换到模拟数据模式：${reason}`);
  
  // 记录连接状态以便后续检测重连
  wasEverConnected = wasEverConnected || false;
};

/**
 * 启动自动重试连接
 * @param {Function} onConnected - 连接成功时的回调
 */
export const startConnectionRetry = (onConnected = null) => {
  // 清除已有的重试计时器
  if (checkTimer) {
    clearInterval(checkTimer);
  }
  
  // 存储回调
  if (onConnected) {
    onConnectedCallback = onConnected;
  }
  
  // 立即执行一次检查
  checkBackendConnection();
  
  // 设置重试计时器
  checkTimer = setInterval(async () => {
    // 如果已连接，不需要重试
    if (!window._useMockData) {
      clearInterval(checkTimer);
      checkTimer = null;
      return;
    }
    
    // 达到最大重试次数，停止重试
    if (retryCount >= MAX_RETRIES) {
      console.warn('后端连接重试次数已达上限，不再尝试连接');
      clearInterval(checkTimer);
      checkTimer = null;
      return;
    }
    
    console.log(`尝试重新连接后端服务 (${retryCount + 1}/${MAX_RETRIES})...`);
    retryCount++;
    
    const connected = await checkBackendConnection();
    if (connected) {
      console.log('后端服务连接成功，停止重试');
      clearInterval(checkTimer);
      checkTimer = null;
    }
  }, CHECK_INTERVAL);
  
  // 返回清理函数
  return () => {
    if (checkTimer) {
      clearInterval(checkTimer);
      checkTimer = null;
    }
  };
};

/**
 * 停止连接重试
 */
export const stopConnectionRetry = () => {
  if (checkTimer) {
    clearInterval(checkTimer);
    checkTimer = null;
  }
  retryCount = 0;
};

export default {
  checkBackendConnection,
  startConnectionRetry,
  stopConnectionRetry
};

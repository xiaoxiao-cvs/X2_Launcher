import axios from 'axios';

/**
 * 获取所有实例列表
 * @returns {Promise<Array>} 实例列表
 */
export const fetchInstances = async () => {
  try {
    const response = await axios.get('/api/instances');
    if (response.data && response.data.instances) {
      return response.data.instances;
    }
    return [];
  } catch (error) {
    console.error('获取实例列表失败:', error);
    throw new Error('获取实例列表失败');
  }
};

/**
 * 获取系统状态
 * @returns {Promise<Object>} 系统状态
 */
export const fetchSystemStatus = async () => {
  try {
    const response = await axios.get('/api/status');
    return response.data || {};
  } catch (error) {
    console.error('获取系统状态失败:', error);
    throw new Error('获取系统状态失败');
  }
};

/**
 * 启动实例
 * @param {string} instanceName 实例名称
 * @returns {Promise<Object>} 启动结果
 */
export const startInstance = async (instanceName) => {
  try {
    const response = await axios.post(`/api/start/${instanceName}`);
    return response.data;
  } catch (error) {
    console.error('启动实例失败:', error);
    throw new Error(error.response?.data?.detail || '启动实例失败');
  }
};

/**
 * 停止实例
 * @returns {Promise<Object>} 停止结果
 */
export const stopInstance = async () => {
  try {
    const response = await axios.post('/api/stop');
    return response.data;
  } catch (error) {
    console.error('停止实例失败:', error);
    throw new Error(error.response?.data?.detail || '停止实例失败');
  }
};

/**
 * 启动NapCat服务
 * @param {string} instanceName 实例名称
 * @returns {Promise<Object>} 启动结果
 */
export const startNapcat = async (instanceName) => {
  try {
    const response = await axios.post(`/api/start/${instanceName}/napcat`);
    return response.data;
  } catch (error) {
    console.error('启动NapCat失败:', error);
    throw new Error(error.response?.data?.detail || '启动NapCat失败');
  }
};

/**
 * 启动NoneBot服务
 * @param {string} instanceName 实例名称
 * @returns {Promise<Object>} 启动结果
 */
export const startNonebot = async (instanceName) => {
  try {
    const response = await axios.post(`/api/start/${instanceName}/nonebot`);
    return response.data;
  } catch (error) {
    console.error('启动NoneBot失败:', error);
    throw new Error(error.response?.data?.detail || '启动NoneBot失败');
  }
};

/**
 * 更新实例
 * @param {string} instanceName 实例名称
 * @returns {Promise<Object>} 更新结果
 */
export const updateInstance = async (instanceName) => {
  try {
    const response = await axios.post(`/api/update/${instanceName}`);
    return response.data;
  } catch (error) {
    console.error('更新实例失败:', error);
    throw new Error('更新实例失败');
  }
};

/**
 * 删除实例
 * @param {string} instanceName 实例名称
 * @returns {Promise<Object>} 删除结果
 */
export const deleteInstance = async (instanceName) => {
  try {
    const response = await axios.delete(`/api/instance/${instanceName}`);
    return response.data;
  } catch (error) {
    console.error('删除实例失败:', error);
    throw new Error('删除实例失败');
  }
};

/**
 * 打开文件夹
 * @param {string} path 文件夹路径
 * @returns {Promise<void>}
 */
export const openFolder = async (path) => {
  try {
    await axios.post('/api/open-folder', { path });
  } catch (error) {
    console.error('无法打开文件夹:', error);
    throw new Error('无法打开文件夹');
  }
};

/**
 * 获取系统性能指标
 * @returns {Promise<Object>} 性能指标
 */
export const fetchSystemMetrics = async () => {
  try {
    // 优先从electronAPI获取
    if (window.electronAPI && typeof window.electronAPI.getSystemMetrics === 'function') {
      return await window.electronAPI.getSystemMetrics();
    }
    
    // 备用：发起API请求获取
    const response = await axios.get('/api/metrics');
    return response.data;
  } catch (error) {
    console.error('获取系统性能指标失败:', error);
    
    // 返回模拟数据
    return {
      cpu: { 
        usage: Math.random() * 30 + 20,
        cores: 8,
        frequency: 3200,
        model: 'CPU 模拟数据' 
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
};

export default {
  fetchInstances,
  fetchSystemStatus,
  startInstance,
  stopInstance,
  startNapcat,
  startNonebot,
  updateInstance,
  deleteInstance,
  openFolder,
  fetchSystemMetrics
};

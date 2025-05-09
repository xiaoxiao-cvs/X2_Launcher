import axios from 'axios';
import { ElMessage } from 'element-plus';

/**
 * 获取可用的版本列表
 * @returns {Promise<Array<string>>} 版本列表
 */
export const fetchVersions = async () => {
  try {
    // 首先尝试标准API路径
    console.log('尝试获取版本列表: /api/versions');
    const response = await axios.get('/api/versions');
    if (response.data && response.data.versions) {
      console.log('成功获取版本列表:', response.data.versions);
      return response.data.versions;
    }
    return [];
  } catch (error) {
    console.error('获取版本列表失败:', error);
    // 尝试备用路径
    try {
      console.log('尝试备用路径: /versions');
      const fallbackResponse = await axios.get('/versions');
      if (fallbackResponse.data && fallbackResponse.data.versions) {
        console.log('通过备用路径成功获取版本列表:', fallbackResponse.data.versions);
        return fallbackResponse.data.versions;
      }
    } catch (fallbackError) {
      console.error('备用路径获取版本列表失败:', fallbackError);
    }
    throw new Error('获取版本列表失败');
  }
};

/**
 * 部署指定版本
 * @param {string} version 版本号
 * @param {string} instanceName 实例名称
 * @returns {Promise<Object>} 部署结果
 */
export const deployVersion = async (version, instanceName) => {
  console.log(`开始部署版本 ${version}, 实例名称: ${instanceName}`);
  
  // 构造请求数据
  const requestData = {
    version,
    instance_name: instanceName
  };
  
  // 尝试多种请求方式
  const endpoints = [
    { url: '/api/deploy', method: 'post', data: requestData },
    { url: '/deploy', method: 'post', data: requestData },
    { url: `/api/deploy/${version}`, method: 'post', data: { instance_name: instanceName } },
    { url: `/deploy/${version}`, method: 'post', data: { instance_name: instanceName } }
  ];
  
  let lastError = null;
  
  // 按顺序尝试各个端点
  for (const endpoint of endpoints) {
    try {
      console.log(`尝试请求: ${endpoint.method.toUpperCase()} ${endpoint.url}`);
      const response = await axios({
        url: endpoint.url,
        method: endpoint.method,
        data: endpoint.data,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }
      });
      
      console.log(`请求成功: ${endpoint.url}`, response.data);
      return response.data;
    } catch (error) {
      console.warn(`请求失败: ${endpoint.url}`, error);
      lastError = error;
      
      // 查看错误详情以便调试
      if (error.response) {
        console.error('响应状态:', error.response.status);
        console.error('响应数据:', error.response.data);
      } else if (error.request) {
        console.error('无响应:', error.request);
      } else {
        console.error('请求配置错误:', error.message);
      }
    }
  }
  
  // 所有请求都失败
  console.error('所有部署请求都失败');
  return {
    success: false,
    message: lastError?.response?.data?.detail || lastError?.message || '部署版本失败'
  };
};

/**
 * 检查部署状态
 * @param {string} instanceName 实例名称
 * @returns {Promise<Object>} 部署状态
 */
export const checkDeployStatus = async (instanceName) => {
  try {
    const response = await axios.get(`/api/deploy/status/${instanceName}`);
    return response.data;
  } catch (error) {
    console.error('检查部署状态失败:', error);
    throw new Error('检查部署状态失败');
  }
};

/**
 * 配置Bot
 * @param {Object} config 配置对象
 * @returns {Promise<Object>} 配置结果
 */
export const configureBot = async (config) => {
  try {
    // 更新API路径以匹配后端路由 /api/install/configure
    const response = await axios.post('/api/install/configure', config);
    return response.data;
  } catch (error) {
    console.error('配置Bot失败:', error);
    return {
      success: false,
      message: error.response?.data?.detail || error.message || '配置Bot失败'
    };
  }
};

/**
 * 检查安装状态
 * @returns {Promise<Object>} 安装状态
 */
export const checkInstallStatus = async () => {
  try {
    const response = await axios.get('/api/install-status');
    return response.data;
  } catch (error) {
    console.error('检查安装状态失败:', error);
    return {
      napcat_installing: false,
      nonebot_installing: false
    };
  }
};

export default {
  fetchVersions,
  deployVersion,
  checkDeployStatus,
  configureBot,
  checkInstallStatus
};

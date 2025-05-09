import axios from 'axios';

/**
 * 获取可用的MaiBot版本列表
 * @returns {Promise<Array>} 版本列表
 */
export const fetchVersions = async () => {
  try {
    const response = await axios.get('/api/versions');
    if (response.data && response.data.versions) {
      return response.data.versions;
    }
    return [];
  } catch (error) {
    console.error('获取版本列表失败:', error);
    throw new Error('获取版本列表失败');
  }
};

/**
 * 部署指定版本的MaiBot
 * @param {string} version 要部署的版本
 * @returns {Promise<Object>} 部署结果
 */
export const deployVersion = async (version) => {
  try {
    const response = await axios.post(`/api/deploy/${version}`);
    return response.data;
  } catch (error) {
    console.error('部署版本失败:', error);
    throw new Error(error.response?.data?.detail || '部署版本失败');
  }
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
 * 配置Bot实例
 * @param {Object} config 配置信息
 * @returns {Promise<Object>} 配置结果
 */
export const configureBot = async (config) => {
  try {
    const response = await axios.post('/api/install/configure', config);
    return response.data;
  } catch (error) {
    console.error('配置Bot失败:', error);
    throw new Error(error.response?.data?.detail || '配置Bot失败');
  }
};

/**
 * 获取安装状态
 * @returns {Promise<Object>} 安装状态
 */
export const checkInstallStatus = async () => {
  try {
    const response = await axios.get('/api/install/status');
    return response.data;
  } catch (error) {
    console.error('检查安装状态失败:', error);
    throw new Error('检查安装状态失败');
  }
};

export default {
  fetchVersions,
  deployVersion,
  checkDeployStatus,
  configureBot,
  checkInstallStatus
};

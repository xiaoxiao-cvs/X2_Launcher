/**
 * 日志解析工具
 * 用于识别安装流程中的关键信息和状态
 */

/**
 * 判断日志是否表示安装完成
 * @param {Object} log - 日志对象
 * @returns {boolean} - 是否表示安装完成
 */
export const isInstallationComplete = (log) => {
  if (!log || !log.message) return false;
  
  const message = log.message.toLowerCase();
  const completeKeywords = [
    '安装完成',
    '配置完成',
    '初始化完成',
    'installation complete',
    'setup finished',
    '依赖安装成功',
    'successfully installed',
    '已成功安装',
    '安装过程已完成',
    '所有组件已安装',
    'bot已准备就绪',
    '部署完成',
    '配置已生效'
  ];
  
  return completeKeywords.some(keyword => message.includes(keyword));
};

/**
 * 判断日志是否表示安装错误
 * @param {Object} log - 日志对象
 * @returns {boolean} - 是否表示安装错误
 */
export const isInstallationError = (log) => {
  if (!log || !log.message) return false;
  
  // 如果日志级别明确是ERROR
  if (log.level && log.level.toUpperCase() === 'ERROR') return true;
  
  const message = log.message.toLowerCase();
  const errorKeywords = [
    '安装失败',
    '配置失败',
    '错误:',
    'error:',
    'exception',
    '异常',
    'failed to',
    '无法完成',
    '不能继续',
    '中断',
    'traceback'
  ];
  
  return errorKeywords.some(keyword => message.includes(keyword));
};

/**
 * 判断是否是重要日志
 * @param {Object} log - 日志对象
 * @returns {boolean} - 是否是重要日志
 */
export const isImportantLog = (log) => {
  if (!log) return false;
  
  // 检查日志级别
  if (log.level) {
    const level = log.level.toLowerCase();
    if (level === 'error' || level === 'warning' || level === 'success') {
      return true;
    }
  }
  
  // 检查日志来源
  if (log.source === 'command') return true;
  
  // 检查消息内容
  if (log.message) {
    const message = log.message.toLowerCase();
    
    // 配置和安装关键词
    const importantKeywords = [
      '安装',
      '配置',
      '启动',
      '完成',
      '成功',
      '失败',
      '错误',
      'installed',
      'configured',
      'started',
      'completed',
      'failed',
      'error'
    ];
    
    return importantKeywords.some(keyword => message.includes(keyword));
  }
  
  return false;
};

/**
 * 获取Shell格式的日志
 * @param {Object} log - 日志对象
 * @returns {string} - 格式化后的日志字符串
 */
export const getShellFormattedLog = (log) => {
  if (!log) return '';
  
  const time = log.time ? `[${log.time}]` : '';
  const level = log.level ? `[${log.level}]` : '';
  const source = log.source ? `[${log.source}]` : '';
  
  return `${time} ${level} ${source} ${log.message || ''}`;
};

export default {
  isInstallationComplete,
  isInstallationError,
  isImportantLog,
  getShellFormattedLog
};

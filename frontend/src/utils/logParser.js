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
    '安装过程已完成'
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
  
  // 检查日志级别
  if (log.level === 'ERROR' || log.level === 'CRITICAL') {
    return true;
  }
  
  const message = log.message.toLowerCase();
  const errorKeywords = [
    '安装失败',
    '配置失败',
    '错误',
    'failed to',
    'error:',
    'exception',
    '异常',
    '失败',
    'failed'
  ];
  
  return errorKeywords.some(keyword => message.includes(keyword));
};

/**
 * 判断日志是否为重要日志
 * @param {Object} log - 日志对象
 * @returns {boolean} - 是否为重要日志
 */
export const isImportantLog = (log) => {
  const level = log.level?.toUpperCase() || '';
  if (['ERROR', 'SUCCESS', 'WARNING', 'CRITICAL'].includes(level)) {
    return true;
  }
  
  // 内容判断
  if (isInstallationComplete(log) || isInstallationError(log)) {
    return true;
  }
  
  const message = log.message?.toLowerCase() || '';
  const importantKeywords = [
    'installed',
    '已安装',
    'starting',
    '开始',
    'finished',
    '完成',
    'downloading',
    '下载',
    'extracting',
    '解压',
    'configuring',
    '配置',
    'initializing',
    '初始化',
    'pip',
    'python',
    'requirement',
    'install',
    '依赖',
    'clone',
    'collecting',
    '正在安装',
    'cloning',
    'github',
    'notice:',
    'napcat',    
    'nonebot',    
    'websocket',    
    '虚拟环境',    
    'bot启动',    
    '端口',    
    '成功连接',    
    'fastapi',    
    'onebot',    
    '启动完成',    
    '监听',    
    'git clone',    
    'maibot', 
    'error',
    '错误',
    '失败',
    'failed',
    'exception',
    '异常',
    'warning',
    '警告'
  ];
  
  return importantKeywords.some(keyword => message.includes(keyword));
};

/**
 * 获取日志的Shell风格格式
 * @param {Object} log - 日志对象 
 * @returns {Object} - 包含格式化后的Shell风格日志
 */
export const getShellFormattedLog = (log) => {
  if (!log) return '';
  
  let prefix = '';
  const source = log.source?.toLowerCase() || '';
  
  switch(source) {
    case 'pip': prefix = '[pip] '; break;
    case 'python': prefix = '[python] '; break;
    case 'system': prefix = '[system] '; break;
    case 'command': prefix = '$ '; break;
    default: prefix = source ? `[${source}] ` : '';
  }
  
  return `${prefix}${log.message || ''}`;
};

/**
 * 获取日志的可读级别名称
 * @param {string} level - 日志级别
 * @returns {string} - 可读的日志级别名称
 */
export const getReadableLogLevel = (level) => {
  if (!level) return 'INFO';
  
  const normalizedLevel = level.toUpperCase();
  
  switch (normalizedLevel) {
    case 'DEBUG': return '调试';
    case 'INFO': return '信息';
    case 'WARNING': return '警告';
    case 'ERROR': return '错误';
    case 'CRITICAL': return '严重';
    case 'SUCCESS': return '成功';
    default: return normalizedLevel;
  }
};

export default {
  isInstallationComplete,
  isInstallationError,
  isImportantLog,
  getShellFormattedLog,
  getReadableLogLevel
};

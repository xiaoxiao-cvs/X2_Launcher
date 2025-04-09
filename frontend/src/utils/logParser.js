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
  if (!log) return false;
  
  const message = log.message?.toLowerCase() || '';
  
  // 安装完成的关键词 - 增加更多匹配词
  const completionKeywords = [
    '安装完成',
    '请运行启动脚本',
    'successfully installed',
    '依赖安装成功',
    'installation complete',
    'installation finished',
    'installation succeeded',
    '安装已完成',
    '安装已结束',
    '安装成功',
    '依赖已安装',
    '已安装完成',
    '初始化成功',
    'setup complete',
    'nonebot 已启动', // 添加NoneBot启动成功识别
    'napcat 已启动',  // 添加NapCat启动成功识别
    'bot已成功启动'    // 添加Bot启动成功识别
  ];
  
  // 判断日志内容是否表示完成消息
  const hasCompletionKeyword = completionKeywords.some(keyword => message.includes(keyword));
  
  // 特殊处理最终安装成功的消息
  if (message.includes('安装完成！请运行启动脚本')) {
    return true;
  }
  
  // 处理pip安装成功日志
  if (message.startsWith('successfully installed') && message.includes('pip')) {
    return true;
  }
  
  return hasCompletionKeyword;
};

/**
 * 判断日志是否表示安装错误
 * @param {Object} log - 日志对象
 * @returns {boolean} - 是否表示安装错误
 */
export const isInstallationError = (log) => {
  if (!log) return false;
  
  const message = log.message?.toLowerCase() || '';
  const level = log.level?.toLowerCase() || '';
  
  // 错误级别判断
  if (level === 'error') return true;
  
  // 错误关键词 - 增加更多可能的错误指示
  const errorKeywords = [
    'error:',
    'failed to',
    'installation failed',
    '安装失败',
    'cannot find',
    'not found',
    'could not',
    'no such file',
    'permission denied',
    '权限被拒绝',
    'exception occurred',
    'fatal:',
    'errno',
    'does not appear',
    '不存在',
    '无法访问',
    'cannot access',
    'command not found',
    '启动失败',       // 添加启动失败识别
    'connection refused', // 添加连接拒绝错误识别
    '无法连接'         // 添加无法连接错误识别
  ];
  
  // 特殊过滤：有些错误消息不是真正的失败
  if (message.includes("does not appear to be a python project") && 
      message.includes("neither 'setup.py' nor 'pyproject.toml' found") &&
      message.includes("error:")) {
    return false; // 这是相对路径导致的警告，不是真正的错误
  }
  
  return errorKeywords.some(keyword => message.includes(keyword));
};

/**
 * 判断日志是否为重要日志
 * @param {Object} log - 日志对象
 * @returns {boolean} - 是否为重要日志
 */
export const isImportantLog = (log) => {
  if (!log) return false;
  
  // 级别判断
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
    'napcat',       // 添加识别NapCat关键词
    'nonebot',      // 添加识别NoneBot关键词 
    'websocket',    // 添加识别websocket关键词
    '虚拟环境',      // 添加识别虚拟环境关键词
    'bot启动',       // 添加识别Bot启动关键词
    '端口',          // 添加识别端口配置关键词
    '成功连接',       // 添加识别连接成功关键词
    'fastapi',      // 添加识别FastAPI关键词
    'onebot',       // 添加识别OneBot关键词
    '启动完成',       // 添加启动完成关键词
    '监听',          // 添加监听端口关键词
    'git clone',    // 添加Git克隆关键词
    'maibot'        // 添加MaiBot关键词
  ];
  
  return importantKeywords.some(keyword => message.includes(keyword));
};

/**
 * 获取日志的Shell风格格式
 * @param {Object} log - 日志对象 
 * @returns {Object} - 包含格式化后的Shell风格日志
 */
export const getShellFormattedLog = (log) => {
  if (!log) return { prefix: '', content: '', isCommand: false };
  
  let prefix = '';
  let content = log.message || '';
  let isCommand = false;
  
  // 根据日志源和级别设置前缀
  const source = log.source?.toLowerCase() || 'system';
  const level = log.level?.toLowerCase() || 'info';
  
  // 判断是否为命令行输入
  if (content.startsWith('$') || content.startsWith('#') || content.startsWith('>')) {
    isCommand = true;
    return { prefix: '', content, isCommand };
  }
  
  // 根据日志源设置前缀
  switch (source) {
    case 'pip':
      prefix = '[pip] ';
      break;
    case 'python':
      prefix = '[python] ';
      break;
    case 'install':
      prefix = '[install] ';
      break;
    case 'napcat':
      prefix = '[napcat] ';
      break;
    case 'nonebot':
      prefix = '[nonebot] ';
      break;
    case 'bot':
      prefix = '[maibot] ';   // 添加Bot前缀
      break;
    case 'venv':
      prefix = '[venv] ';     // 添加虚拟环境前缀
      break;
    default:
      prefix = '[system] ';
  }
  
  // 根据日志级别添加颜色类
  const logClass = level === 'error' ? 'error' : 
                   level === 'warning' ? 'warning' : 
                   level === 'success' ? 'success' : 'info';
  
  return { prefix, content, logClass, isCommand };
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

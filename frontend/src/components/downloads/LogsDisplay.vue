<template>
  <div class="section">
    <div class="section-title">
      <div class="log-title-container">
        <span>安装日志</span>
        <div class="log-actions">
          <el-switch
            v-model="autoScroll"
            active-text="自动滚动"
            inactive-text=""
            inline-prompt
            size="small"
          ></el-switch>
          <el-button size="small" @click="clearLogs">清空日志</el-button>
          <el-button size="small" type="primary" @click="exportLogs">导出日志</el-button>
        </div>
      </div>
    </div>
    <div class="shell-container" ref="logsContainer">
      <div v-if="logs.length === 0" class="empty-logs">
        <el-empty description="暂无日志" :image-size="100"></el-empty>
      </div>
      <div v-else class="terminal">
        <div class="terminal-header">
          <div class="terminal-controls">
            <span class="control close"></span>
            <span class="control minimize"></span>
            <span class="control maximize"></span>
          </div>
          <div class="terminal-title">安装终端</div>
        </div>
        <div class="terminal-body">
          <div v-for="(log, index) in logs" :key="index" 
               :class="['terminal-line', getShellLogClass(log)]">
            <template v-if="isCommandLine(log)">
              <span class="command-prompt">$ </span>
              <span class="command-content">{{ log.message }}</span>
            </template>
            <template v-else>
              <span v-if="showTimestamps" class="timestamp">{{ log.time || formatTime(new Date()) }}</span>
              <span :class="['prefix', getSourceClass(log)]">{{ getShellPrefix(log) }}</span>
              <span :class="['content', getContentClass(log)]">{{ log.message }}</span>
            </template>
          </div>
        </div>
      </div>
    </div>
    <div class="terminal-options">
      <el-checkbox v-model="showTimestamps" size="small">显示时间戳</el-checkbox>
    </div>
  </div>
</template>

<script setup>
import { ref, defineProps, defineEmits, watch, nextTick } from 'vue';
import { ElMessage } from 'element-plus';
import { isImportantLog, getShellFormattedLog } from '../../utils/logParser.js';

const props = defineProps({
  logs: {
    type: Array,
    required: true
  }
});

const emit = defineEmits(['clear-logs']);

const logsContainer = ref(null);
const autoScroll = ref(true);
const showTimestamps = ref(false);

// 清空日志
const clearLogs = () => {
  emit('clear-logs');
};

// 导出所有日志
const exportLogs = () => {
  if (props.logs.length === 0) {
    ElMessage.warning('没有日志可导出');
    return;
  }
  
  // 格式化日志内容
  const logContent = props.logs.map(log => 
    `[${log.time || ''}] [${log.source}] [${log.level}] ${log.message}`
  ).join('\n');
  
  // 创建Blob对象
  const blob = new Blob([logContent], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  
  // 创建下载链接
  const a = document.createElement('a');
  a.href = url;
  a.download = `install-log-${formatDateForFile(new Date())}.txt`;
  document.body.appendChild(a);
  a.click();
  
  // 清理
  setTimeout(() => {
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, 100);
};

// 检查是否是命令行
const isCommandLine = (log) => {
  if (!log || !log.message) return false;
  const msg = log.message.trim();
  return msg.startsWith('$') || 
         msg.startsWith('>') || 
         msg.startsWith('#') || 
         log.source === 'command';
};

// 获取Shell日志类
const getShellLogClass = (log) => {
  if (isImportantLog(log)) return 'important-line';
  if (isCommandLine(log)) return 'command-line';
  return '';
};

// 获取Shell前缀
const getShellPrefix = (log) => {
  if (!log) return '';
  
  const source = log.source?.toLowerCase();
  switch(source) {
    case 'pip': return '[pip]';
    case 'python': return '[python]';
    case 'napcat': return '[napcat]';
    case 'nonebot': return '[nonebot]';
    case 'install': return '[install]';
    default: return '[system]';
  }
};

// 获取日志源样式类
const getSourceClass = (log) => {
  if (!log) return '';
  const source = log.source?.toLowerCase();
  return source || '';
};

// 获取内容样式类
const getContentClass = (log) => {
  if (!log) return '';
  
  const level = log.level?.toLowerCase();
  if (level === 'error') return 'error';
  if (level === 'warning') return 'warning';
  if (level === 'success') return 'success';
  return '';
};

// 格式化时间为文件名
function formatDateForFile(date) {
  return date.toISOString().slice(0, 19).replace(/[T:]/g, '-');
}

// 格式化时间展示
function formatTime(date) {
  return date.toLocaleString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit', 
    second: '2-digit'
  });
}

// 自动滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (logsContainer.value) {
      logsContainer.value.scrollTop = logsContainer.value.scrollHeight;
    }
  });
};

// 观察日志变化，自动滚动
watch(() => props.logs.length, () => {
  if (autoScroll.value) {
    scrollToBottom();
  }
});

// 使用导入的方法替换本地方法
const isLogImportant = (log) => isImportantLog(log);
</script>

<style scoped>
.log-title-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.log-actions {
  display: flex;
  gap: 8px;
}

.shell-container {
  max-height: 500px;
  overflow-y: auto;
  border-radius: 8px;
  background: var(--el-fill-color-lighter, #f5f5f5);
}

/* 终端样式 */
.terminal {
  background: var(--terminal-bg, #0d0d0d);
  border-radius: 6px;
  overflow: hidden;
  font-family: 'Courier New', Courier, monospace;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.terminal-header {
  background: #323233;
  padding: 8px 16px;
  display: flex;
  align-items: center;
}

.terminal-controls {
  display: flex;
  gap: 6px;
  margin-right: 16px;
}

.control {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.close {
  background-color: #ff605c;
}

.minimize {
  background-color: #ffbd44;
}

.maximize {
  background-color: #00ca4e;
}

.terminal-title {
  color: var(--terminal-text, #d9d9d9);
  font-size: 13px;
  flex: 1;
  text-align: center;
}

.terminal-body {
  padding: 12px;
  color: var(--terminal-text, #d9d9d9);
  font-size: 14px;
}

.terminal-line {
  line-height: 1.4;
  margin-bottom: 6px;
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
}

.command-prompt {
  color: #77e083;
  margin-right: 5px;
}

.command-content {
  color: var(--terminal-text, #d9d9d9);
}

.command-line {
  margin-top: 8px;
  margin-bottom: 8px;
  background-color: rgba(255, 255, 255, 0.05);
  padding: 2px 0;
}

.important-line {
  background-color: rgba(65, 105, 225, 0.1);
  font-weight: 500;
  border-left: 2px solid #4169e1;
  padding-left: 4px;
}

.timestamp {
  color: #888;
  margin-right: 10px;
  font-size: 12px;
  min-width: 80px;
  display: inline-block;
}

.prefix {
  margin-right: 8px;
  font-weight: 600;
  padding: 2px 4px;
  border-radius: 3px;
  min-width: 70px;
  display: inline-block;
  text-align: center;
  font-size: 12px;
}

.prefix.pip {
  color: #2273c3;
  background-color: rgba(34, 115, 195, 0.1);
}

.prefix.python {
  color: #3776ab;
  background-color: rgba(55, 118, 171, 0.1);
}

.prefix.napcat {
  color: #42b983;
  background-color: rgba(66, 185, 131, 0.1);
}

.prefix.nonebot {
  color: #6495ed;
  background-color: rgba(100, 149, 237, 0.1);
}

.prefix.install {
  color: #9370db;
  background-color: rgba(147, 112, 219, 0.1);
}

.prefix.system {
  color: #888;
  background-color: rgba(136, 136, 136, 0.1);
}

.content {
  flex: 1;
  word-break: break-word;
  white-space: pre-wrap;
}

.content.error {
  color: #ff6b6b;
}

.content.warning {
  color: #ffb347;
}

.content.success {
  color: #00ca4e;
}

.empty-logs {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.terminal-options {
  margin-top: 10px;
  display: flex;
  justify-content: flex-end;
}

/* 深色模式下的空日志文本 */
:deep(html.dark-mode) .el-empty__description p {
  color: var(--el-text-color-secondary);
}
</style>

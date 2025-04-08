<template>
  <div class="logs-tab">
    <div class="log-header">
      <h3>日志记录</h3>
      <el-button 
        type="primary" 
        size="small" 
        @click="clearLogs"
        class="clear-btn">
        清空日志
      </el-button>
    </div>
    
    <div class="log-container">
      <div v-for="(log, index) in logs" :key="index" class="log-item">
        <div class="log-icon">
          <el-icon :color="log.type === 'warning' ? '#E6A23C' : '#67C23A'">
            <WarningFilled v-if="log.type === 'warning'" />
            <SuccessFilled v-else />
          </el-icon>
        </div>
        <div class="log-content">
          <span class="log-time">{{ log.time }}</span>
          <span class="log-message">{{ log.message }}</span>
        </div>
        <div class="log-action">
          <el-button size="small" text @click="copyLog(log.message)">
            <el-icon><DocumentCopy /></el-icon>
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { WarningFilled, SuccessFilled, DocumentCopy } from '@element-plus/icons-vue'

const logs = ref([
  {
    type: 'warning',
    time: '2025-4-8 2:25:10',
    message: 'No connection could be made because the target machine actively refused it.'
  },
  {
    type: 'info',
    time: '2025-4-8 2:25:17',
    message: 'MongoDB initialized successfully'
  },
  {
    type: 'info',
    time: '2025-4-8 2:25:25',
    message: 'NapCat initialized successfully'
  },
])

const copyLog = (message) => {
  navigator.clipboard.writeText(message)
    .then(() => {
      ElMessage.success('日志已复制')
    })
    .catch(err => {
      ElMessage.error('复制失败')
      console.error('复制失败:', err)
    })
}

const clearLogs = () => {
  logs.value = []
  ElMessage.success('日志已清空')
}
</script>

<style scoped>
.logs-tab {
  width: 100%;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.log-container {
  background: #f9f9f9;
  border-radius: 8px;
  padding: 12px;
}

.log-item {
  display: flex;
  padding: 8px;
  border-bottom: 1px solid #eee;
  align-items: flex-start;
}

.log-icon {
  margin-right: 10px;
}

.log-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.log-time {
  font-size: 0.8em;
  color: #999;
  margin-bottom: 4px;
}

.log-message {
  word-break: break-word;
}

.log-action {
  margin-left: 8px;
}
</style>

<template>
  <el-card shadow="hover" class="status-card">
    <template #header>
      <div class="card-header">
        <span>系统性能</span>
        <div class="header-right">
          <el-tag v-if="performanceError" type="warning" size="small" effect="light" class="error-tag">
            数据异常
          </el-tag>
          <el-button 
            circle
            type="primary"
            size="small" 
            :icon="Refresh"
            @click="refreshPerformance"
            :loading="isRefreshing"
            class="refresh-btn">
          </el-button>
        </div>
      </div>
    </template>
    <div class="performance-dashboard">
      <!-- CPU使用率 -->
      <div class="metric-item">
        <div class="metric-header">
          <el-icon><Cpu /></el-icon>
          <span>CPU使用率</span>
          <span class="metric-value">{{ performance.cpu.usage }}%</span>
        </div>
        <el-progress 
          :percentage="performance.cpu.usage" 
          :color="getProgressColor(performance.cpu.usage)"
          :show-text="false"
          :stroke-width="12"/>
        <div class="metric-details">
          <span>核心数: {{ performance.cpu.cores }}</span>
          <span>频率: {{ (performance.cpu.frequency / 1000).toFixed(2) }} GHz</span>
        </div>
      </div>
      
      <!-- 内存使用情况 -->
      <div class="metric-item">
        <div class="metric-header">
          <el-icon><Monitor /></el-icon>
          <span>内存使用</span>
          <span class="metric-value">{{ formatBytes(performance.memory.used) }} / {{ formatBytes(performance.memory.total) }}</span>
        </div>
        <el-progress 
          :percentage="performance.memory.usage" 
          :color="getProgressColor(performance.memory.usage)"
          :show-text="false"
          :stroke-width="12"/>
        <div class="metric-details">
          <span>可用: {{ formatBytes(performance.memory.free) }}</span>
        </div>
      </div>
      
      <!-- 网络活动 -->
      <div class="metric-item">
        <div class="metric-header">
          <el-icon><Connection /></el-icon>
          <span>网络活动</span>
        </div>
        <div class="network-stats">
          <span>上传: {{ formatBytes(performance.network.sentRate) }}/s</span>
          <span>下载: {{ formatBytes(performance.network.receivedRate) }}/s</span>
        </div>
        <div class="metric-details">
          <span>总上传: {{ formatBytes(performance.network.sent) }}</span>
          <span>总下载: {{ formatBytes(performance.network.received) }}</span>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { Cpu, Monitor, Connection, RefreshRight as Refresh } from '@element-plus/icons-vue'

// 性能监控相关
const performance = ref({
  cpu: { usage: 0, cores: 0, frequency: 0 },
  memory: { total: 0, used: 0, free: 0, usage: 0 },
  network: { sent: 0, received: 0, sentRate: 0, receivedRate: 0 }
})
const isRefreshing = ref(false)
const performanceError = ref(null)
let refreshInterval = null

// 格式化字节
const formatBytes = (bytes, decimals = 2) => {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(Math.abs(bytes)) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`
}

// 刷新性能数据
const refreshPerformance = async () => {
  if (isRefreshing.value) return;
  
  isRefreshing.value = true;
  performanceError.value = null;
  
  try {
    console.log('正在请求系统性能数据...');
    const result = await window.electronAPI.getSystemMetrics().catch(err => {
      console.error('IPC调用异常:', err);
      throw new Error(`IPC错误: ${err.message || '未知错误'}`);
    });
    
    console.log('接收到性能数据:', result);
    
    if (result?.error) {
      throw new Error(result.message || '获取性能数据失败');
    }
    
    // 计算网络速率
    if (performance.value.network?.sent && result.network) {
      result.network.sentRate = Math.max(0, (result.network.sent - performance.value.network.sent) / 5);
      result.network.receivedRate = Math.max(0, (result.network.received - performance.value.network.received) / 5);
    } else if (result.network) {
      // 首次没有之前的数据，设置为0
      result.network.sentRate = 0;
      result.network.receivedRate = 0;
    }

    performance.value = result;
  } catch (err) {
    console.error('性能获取错误:', err);
    performanceError.value = err;
    // 仅在没有现有数据时使用回退数据
    if (!performance.value.cpu?.cores) {
      performance.value = getFallbackMetrics();
    }
    // 如果是首次加载失败，显示错误
    if (!performance.value.cpu?.cores) {
      ElMessage.error(`性能监控失败: ${err.message}`);
    }
  } finally {
    isRefreshing.value = false;
  }
}

// 添加获取回退指标的函数
const getFallbackMetrics = () => ({
  cpu: { usage: 25, cores: 4, frequency: 2400 },  // 频率单位统一为MHz
  memory: { 
    total: 16 * 1024 * 1024 * 1024,
    used: 8 * 1024 * 1024 * 1024,
    free: 8 * 1024 * 1024 * 1024,
    usage: 50 
  },
  network: { sent: 0, received: 0, sentRate: 0, receivedRate: 0 }
})

// 获取进度条颜色
const getProgressColor = (percentage) => {
  if (percentage < 60) return '#67C23A'  // 绿色
  if (percentage < 80) return '#E6A23C'  // 黄色
  return '#F56C6C'  // 红色
}

onMounted(() => {
  console.log('PerformanceMonitor mounted');
  // 立即刷新一次性能数据
  refreshPerformance();
  
  // 设置定时刷新
  refreshInterval = setInterval(refreshPerformance, 5000);
})

onBeforeUnmount(() => {
  // 清除定时器
  if (refreshInterval) {
    clearInterval(refreshInterval);
  }
})
</script>

<style scoped>
.status-card {
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  border-radius: 8px;
}
.status-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.error-tag {
  margin-right: 4px;
}

.refresh-btn {
  font-size: 14px;
}

.refresh-btn {
  margin-left: auto;
}

/* 性能监控样式 */
.performance-dashboard {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.metric-item {
  padding: 12px;
  background: var(--el-color-primary-light-9);
  border-radius: 8px;
}

.metric-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.metric-header .el-icon {
  margin-right: 8px;
  color: var(--el-color-primary);
}

.metric-value {
  margin-left: auto;
  font-weight: 600;
}

.metric-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 8px;
  font-size: 0.8em;
  color: var(--el-text-color-secondary);
}

.network-stats {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 8px;
  font-size: 0.9em;
}

@media (max-width: 768px) {
  .performance-dashboard {
    grid-template-columns: 1fr;
  }
}
</style>

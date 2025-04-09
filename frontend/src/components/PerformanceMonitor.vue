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
    <div v-if="missingPsutil" class="missing-dep-warning">
      <el-alert
        title="系统监控需要安装psutil模块"
        type="warning"
        :closable="false"
        show-icon
      >
        <template #default>
          <p>缺少psutil模块，系统监控数据为模拟数据</p>
          <el-button size="small" type="primary" @click="installPsutil" :loading="installing">
            安装psutil
          </el-button>
        </template>
      </el-alert>
    </div>
    <div class="performance-dashboard">
      <!-- CPU使用率 -->
      <div class="metric-item">
        <div class="metric-header">
          <el-icon><Cpu /></el-icon>
          <span>CPU使用率</span>
          <span class="metric-value">{{ getCpuUsage() }}%</span>
        </div>
        <el-progress 
          :percentage="getCpuUsage()" 
          :color="getProgressColor(getCpuUsage())"
          :show-text="false"
          :stroke-width="12"/>
        <div class="metric-details">
          <span>核心数: {{ performance.cpu?.cores || 0 }}</span>
          <span>频率: {{ formatCpuFrequency(performance.cpu?.frequency) }}</span>
        </div>
      </div>
      
      <!-- 内存使用情况 -->
      <div class="metric-item">
        <div class="metric-header">
          <el-icon><Monitor /></el-icon>
          <span>内存使用</span>
          <span class="metric-value">{{ formatBytes(getMemoryUsed()) }} / {{ formatBytes(getMemoryTotal()) }}</span>
        </div>
        <el-progress 
          :percentage="getMemoryPercent()" 
          :color="getProgressColor(getMemoryPercent())"
          :show-text="false"
          :stroke-width="12"/>
        <div class="metric-details">
          <span>可用: {{ formatBytes(getMemoryFree()) }}</span>
        </div>
      </div>
      
      <!-- 网络活动 -->
      <div class="metric-item">
        <div class="metric-header">
          <el-icon><Connection /></el-icon>
          <span>网络活动</span>
        </div>
        <div class="network-stats">
          <span>上传: {{ formatBytes(performance.network?.sentRate || 0) }}/s</span>
          <span>下载: {{ formatBytes(performance.network?.receivedRate || 0) }}/s</span>
        </div>
        <div class="metric-details">
          <span>总上传: {{ formatBytes(performance.network?.sent || 0) }}</span>
          <span>总下载: {{ formatBytes(performance.network?.received || 0) }}</span>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { Cpu, Monitor, Connection, RefreshRight as Refresh } from '@element-plus/icons-vue'
import axios from 'axios'

// 性能监控相关
const performance = ref({
  cpu: { usage: 0, cores: 0, frequency: 0, percent: 0 },
  memory: { total: 0, used: 0, free: 0, usage: 0, percent: 0 },
  network: { sent: 0, received: 0, sentRate: 0, receivedRate: 0 }
})
const isRefreshing = ref(false)
const performanceError = ref(null)
const missingPsutil = ref(false);
const installing = ref(false);
let refreshInterval = null

// 获取CPU使用率
const getCpuUsage = () => {
  // 检查不同可能的属性名
  if (performance.value.cpu?.usage !== undefined) return performance.value.cpu.usage;
  if (performance.value.cpu?.percent !== undefined) return performance.value.cpu.percent;
  return 0;
}

// 获取内存总量
const getMemoryTotal = () => {
  return performance.value.memory?.total || 0;
}

// 获取已用内存
const getMemoryUsed = () => {
  return performance.value.memory?.used || 0;
}

// 获取可用内存
const getMemoryFree = () => {
  if (performance.value.memory?.free !== undefined) return performance.value.memory.free;
  if (performance.value.memory?.total && performance.value.memory?.used) {
    return performance.value.memory.total - performance.value.memory.used;
  }
  return 0;
}

// 获取内存使用百分比
const getMemoryPercent = () => {
  if (performance.value.memory?.usage !== undefined) return performance.value.memory.usage;
  if (performance.value.memory?.percent !== undefined) return performance.value.memory.percent;
  if (performance.value.memory?.used && performance.value.memory?.total && performance.value.memory.total > 0) {
    return Math.round((performance.value.memory.used / performance.value.memory.total) * 100);
  }
  return 0;
}

// 格式化字节
const formatBytes = (bytes, decimals = 2) => {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(Math.abs(bytes)) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`
}

// 格式化CPU频率
const formatCpuFrequency = (frequency) => {
  if (!frequency || isNaN(frequency) || frequency === 0) {
    return '未知';
  }
  // 如果frequency已经小于1000，则假设单位为GHz
  if (frequency < 1000) {
    return `${frequency.toFixed(2)} GHz`;
  }
  // 否则假设单位为MHz，转换为GHz
  return `${(frequency / 1000).toFixed(2)} GHz`;
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

    // 检查是否缺少psutil
    if (result?.missing_psutil) {
      missingPsutil.value = true;
      console.log('缺少psutil模块，使用模拟数据');
    } else {
      missingPsutil.value = false;
    }
    
    // 计算网络速率
    if (performance.value.network?.sent && result.network) {
      const timeGap = 5; // 假设间隔为5秒
      result.network.sentRate = Math.max(0, (result.network.sent - performance.value.network.sent) / timeGap);
      result.network.receivedRate = Math.max(0, (result.network.received - performance.value.network.received) / timeGap);
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
  cpu: { usage: 25, percent: 25, cores: 4, frequency: 2400 },  // 频率单位统一为MHz
  memory: { 
    total: 16 * 1024 * 1024 * 1024,
    used: 8 * 1024 * 1024 * 1024,
    free: 8 * 1024 * 1024 * 1024,
    usage: 50,
    percent: 50
  },
  network: { sent: 0, received: 0, sentRate: 0, receivedRate: 0 }
})

// 获取进度条颜色
const getProgressColor = (percentage) => {
  if (percentage < 60) return '#67C23A'  // 绿色
  if (percentage < 80) return '#E6A23C'  // 黄色
  return '#F56C6C'  // 红色
}

const installPsutil = async () => {
  installing.value = true;
  try {
    const response = await axios.post('/api/install-dependencies', {
      packages: ['psutil']
    });
    
    if (response.data && response.data.success) {
      ElMessage.success('psutil安装成功，系统监控将在下次刷新时启用');
      // 安装成功后立即刷新以获取真实数据
      setTimeout(() => refreshPerformance(), 1000);
      missingPsutil.value = false;
    } else {
      ElMessage.error('psutil安装失败：' + (response.data?.message || '未知错误'));
    }
  } catch (error) {
    console.error('安装psutil失败:', error);
    ElMessage.error('安装失败：' + (error.response?.data?.message || error.message));
  } finally {
    installing.value = false;
  }
};

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
  background-color: var(--el-bg-color);
  color: var(--el-text-color-primary);
}
.status-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: inherit;
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
  background: var(--el-fill-color-lighter);
  border-radius: 8px;
  color: var(--el-text-color-primary);
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

.missing-dep-warning {
  margin-bottom: 10px;
}

@media (max-width: 768px) {
  .performance-dashboard {
    grid-template-columns: 1fr;
  }
}
</style>

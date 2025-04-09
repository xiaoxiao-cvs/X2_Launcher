<template>
  <el-card shadow="hover" class="status-card">
    <template #header>
      <div class="card-header">
        <span>系统状态</span>
        <el-button 
          size="small" 
          type="primary"
          @click="refreshStatus"
          :loading="refreshing">
          刷新
        </el-button>
      </div>
    </template>
    <div class="card-content">
      <p>MongoDB: <el-tag :type="getStatusType('mongodb')">{{ getStatusText('mongodb') }}</el-tag></p>
      <p>NapCat 服务器: <el-tag :type="getStatusType('napcat')">{{ getStatusText('napcat') }}</el-tag></p>
      <p>NoneBot 适配器: <el-tag :type="getStatusType('nonebot')">{{ getStatusText('nonebot') }}</el-tag></p>
      <p>MaiM-Core: <el-tag :type="getStatusType('maibot')">{{ getStatusText('maibot') }}</el-tag></p>
    </div>
  </el-card>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue';
import { ElMessage } from 'element-plus';
import axios from 'axios';

const services = ref({
  mongodb: { status: 'unknown', info: '' },
  napcat: { status: 'unknown', info: '' },
  nonebot: { status: 'unknown', info: '' },
  maibot: { status: 'unknown', info: '' }
});

const refreshing = ref(false);
let statusInterval = null;

// 获取状态类型
const getStatusType = (service) => {
  const status = services.value[service]?.status || 'unknown';
  switch(status) {
    case 'running': return 'success';
    case 'stopped': return 'info';
    case 'error': return 'danger';
    case 'unknown': return 'warning';
    default: return 'info';
  }
};

// 获取状态文本
const getStatusText = (service) => {
  const status = services.value[service]?.status || 'unknown';
  const info = services.value[service]?.info || '';
  
  switch(status) {
    case 'running': return `运行中${info ? ' - ' + info : ''}`;
    case 'stopped': return '已停止';
    case 'error': return `错误${info ? ' - ' + info : ''}`;
    case 'unknown': return '未知状态';
    default: return status;
  }
};

// 刷新状态
const refreshStatus = async () => {
  refreshing.value = true;
  try {
    const response = await axios.get('/api/status');
    if (response.data) {
      services.value = response.data;
    }
  } catch (error) {
    console.error('获取服务状态失败:', error);
    ElMessage.error('获取服务状态失败');
  } finally {
    refreshing.value = false;
  }
};

// 组件挂载时开始轮询
onMounted(() => {
  refreshStatus();
  statusInterval = setInterval(refreshStatus, 30000); // 每30秒刷新一次
});

// 组件销毁前清理定时器
onBeforeUnmount(() => {
  if (statusInterval) {
    clearInterval(statusInterval);
  }
});
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

.card-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
  color: inherit;
}

/* 确保卡片内的文本颜色正确 */
.status-card p {
  color: var(--el-text-color-primary);
}
</style>

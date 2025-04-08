<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

const performance = ref(null)
const isRefreshing = ref(false)
const performanceError = ref(null)
const lastNetworkMetrics = ref({ sent: 0, received: 0 })

const refreshPerformance = async () => {
  isRefreshing.value = true
  performanceError.value = null
  
  try {
    const metrics = await window.electronAPI.getSystemMetrics()
    
    if (metrics.error) {
      throw new Error(metrics.message || '获取性能数据失败')
    }

    if (lastNetworkMetrics.value.sent > 0) {
      metrics.network.sentRate = (metrics.network.sent - lastNetworkMetrics.value.sent) / 5
      metrics.network.receivedRate = (metrics.network.received - lastNetworkMetrics.value.received) / 5
    }
    
    lastNetworkMetrics.value = {
      sent: metrics.network.sent,
      received: metrics.network.received
    }
    
    performance.value = metrics
  } catch (err) {
    console.error('性能获取错误:', err)
    performanceError.value = err
    performance.value = getFallbackMetrics()
  } finally {
    isRefreshing.value = false
  }
}

const getFallbackMetrics = () => ({
  cpu: { usage: 25, cores: 4, frequency: 2.4 },
  memory: { 
    total: 16 * 1024 * 1024 * 1024,
    used: 8 * 1024 * 1024 * 1024,
    free: 8 * 1024 * 1024 * 1024,
    usage: 50 
  },
  network: { sent: 0, received: 0, sentRate: 0, receivedRate: 0 }
})

// ...existing code...
</script>

<template>
  <el-card shadow="hover" class="status-card">
    <template #header>
      <div class="card-header">
        <span>系统性能</span>
        <el-tag v-if="performanceError" type="danger">异常</el-tag>
        <el-button size="small" @click="refreshPerformance" :loading="isRefreshing">
          刷新
        </el-button>
      </div>
    </template>
    <!-- ...existing template code... -->
  </el-card>
</template>
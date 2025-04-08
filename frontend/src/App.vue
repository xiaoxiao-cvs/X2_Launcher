<template>
  <div class="app-container">
    <!-- 顶部导航栏 -->
    <div class="header">
      <div class="logo-area">
        <div class="logo-icon">
          <!-- 三条蓝色线条组成的三角形图标 -->
          <svg width="24" height="24" viewBox="0 0 24 24">
            <polygon points="12,2 22,22 2,22" fill="#409EFF"/>
          </svg>
        </div>
        <h1>𝕏² Launcher</h1>
      </div>
      
      <div class="action-buttons">
        <el-button type="info" size="small">启动MaiBot主程序</el-button>
        <el-button type="primary" size="small">关闭</el-button>
        <el-button type="primary" size="small">打开 Web GUI</el-button>
        <el-button type="primary" size="small">生成Web GUI随机密码</el-button>
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="main-content">
      <!-- 左侧导航 -->
      <div class="sidebar">
        <el-menu>
          <el-menu-item index="1">
            <el-icon><House /></el-icon>
            <span>首页</span>
          </el-menu-item>
          <el-menu-item index="2">
            <el-icon><Menu /></el-icon>
            <span>实例</span>
          </el-menu-item>
          <el-menu-item index="3">
            <el-icon><Setting /></el-icon>
            <span>设置</span>
          </el-menu-item>
        </el-menu>
      </div>

      <!-- 右侧内容 -->
      <div class="content">
        <div class="log-header">
          <h3>日志</h3>
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
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { 
  House, 
  Menu, 
  Setting, 
  WarningFilled, 
  SuccessFilled, 
  DocumentCopy,
  StarFilled 
} from '@element-plus/icons-vue'

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
</script>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f5f7fa;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  height: 60px;
  background-color: white;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
}

.logo-area {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo-icon {
  display: flex;
  align-items: center;
}

.action-buttons {
  display: flex;
  gap: 10px;
}

.main-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.sidebar {
  width: 200px;
  background-color: white;
  border-right: 1px solid #e6e6e6;
}

.content {
  flex: 1;
  padding: 20px;
  overflow: auto;
}

.log-header {
  margin-bottom: 20px;
}

.log-container {
  background-color: white;
  border-radius: 4px;
  padding: 15px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
}

.log-item {
  display: flex;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
}

.log-item:last-child {
  border-bottom: none;
}

.log-icon {
  margin-right: 15px;
  font-size: 18px;
}

.log-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.log-time {
  font-size: 12px;
  color: #909399;
}

.log-message {
  margin-top: 5px;
}

.log-action {
  margin-left: 15px;
}
</style>
<template>
  <div class="app-container">
    <!-- 调试模式显示 -->
    <div v-if="debugMode" class="debug-info">
      <p>Debug Mode: App Component Loaded</p>
    </div>
    
    <!-- 顶部导航栏 -->
    <AppHeader />

    <!-- 主内容区域 -->
    <div class="main-content">
      <!-- 左侧导航 -->
      <AppSidebar 
        :active-tab="activeTab" 
        @select="handleMenuSelect" 
      />

      <!-- 右侧内容 -->
      <div class="content">
        <transition name="fade" mode="out-in">
          <!-- 首页内容 -->
          <div v-if="activeTab === 'home'" class="tab-content home-tab">
            <h3 class="welcome-title">欢迎使用 𝕏² Launcher</h3>
            <div class="status-cards">
              <SystemStatusCard />
              <PerformanceMonitor />
            </div>
          </div>

          <!-- 日志页内容 -->
          <LogsPanel v-else-if="activeTab === 'logs'" />

          <!-- 下载页内容 -->
          <DownloadsPanel v-else-if="activeTab === 'downloads'" />

          <!-- 其他页内容 -->
          <div v-else class="tab-content">
            <h3>{{ tabTitles[activeTab] || activeTab }}</h3>
            <p>页面内容建设中...</p>
          </div>
        </transition>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import AppHeader from './components/AppHeader.vue'
import AppSidebar from './components/AppSidebar.vue'
import SystemStatusCard from './components/SystemStatusCard.vue'
import PerformanceMonitor from './components/PerformanceMonitor.vue'
import LogsPanel from './components/LogsPanel.vue'
import DownloadsPanel from './components/DownloadsPanel.vue'

// 开发调试模式
const debugMode = ref(false)

// 标签页相关
const activeTab = ref('home')
const tabTitles = {
  home: '首页',
  instances: '实例管理',
  downloads: '下载中心',
  logs: '系统日志',
  settings: '系统设置'
}

// 菜单选择处理
const handleMenuSelect = (index) => {
  activeTab.value = index
}
</script>

<style scoped>
/* 确保根元素可见 */
.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f5f7fa;
}

/* 调试信息样式 */
.debug-info {
  position: fixed;
  top: 0;
  left: 0;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 10px;
  z-index: 9999;
}

/* 主内容区域样式 */
.main-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.content {
  flex: 1;
  padding: 20px;
  overflow: auto;
  background-color: white;
  margin: 16px;
  border-radius: 0 0 8px 0;
}

/* 页面切换动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

/* 状态卡片 */
.status-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  margin-top: 20px;
}

/* 欢迎标题 */
.welcome-title {
  color: var(--el-color-primary);
  margin-bottom: 20px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .status-cards {
    grid-template-columns: 1fr;
  }
  
  .main-content {
    flex-direction: column;
  }
}
</style>
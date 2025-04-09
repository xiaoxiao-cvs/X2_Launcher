<template>
  <div class="header">
    <div class="logo-area">
      <div class="logo-icon">
        <svg width="24" height="24" viewBox="0 0 24 24">
          <polygon points="12,2 22,22 2,22" fill="var(--el-color-primary)" />
        </svg>
      </div>
      <h1>𝕏² Launcher</h1>
    </div>
    
    <div class="action-buttons">
      <el-tooltip content="切换主题" placement="bottom">
        <el-button 
          circle
          size="small"
          @click="toggleDarkMode"
        >
          <el-icon>
            <Moon v-if="isDarkMode" />
            <Sunny v-else />
          </el-icon>
        </el-button>
      </el-tooltip>
    </div>
  </div>
</template>

<script setup>
import { ref, inject, onMounted } from 'vue';
import { Moon, Sunny } from '@element-plus/icons-vue';

// 深色模式状态
const isDarkMode = ref(false);

// 获取事件总线
const emitter = inject('emitter', null);

// 初始化深色模式状态
onMounted(() => {
  const savedDarkMode = localStorage.getItem('darkMode');
  if (savedDarkMode !== null) {
    isDarkMode.value = savedDarkMode === 'true';
  } else {
    // 检查系统偏好
    isDarkMode.value = window.matchMedia('(prefers-color-scheme: dark)').matches;
  }
  
  // 监听主题变化
  if (emitter) {
    emitter.on('dark-mode-changed', (value) => {
      isDarkMode.value = value;
    });
  }
});

// 切换深色模式
const toggleDarkMode = () => {
  isDarkMode.value = !isDarkMode.value;
  localStorage.setItem('darkMode', isDarkMode.value);
  
  // 应用深色模式
  if (isDarkMode.value) {
    document.documentElement.classList.add('dark-mode');
    document.documentElement.setAttribute('data-theme', 'dark');
  } else {
    document.documentElement.classList.remove('dark-mode');
    document.documentElement.setAttribute('data-theme', 'light');
  }
  
  // 通知其他组件
  if (emitter) {
    emitter.emit('dark-mode-changed', isDarkMode.value);
  }
};
</script>

<style scoped>
.header {
  padding: 0 20px;
  background-color: var(--el-bg-color, white);
  border-bottom: 1px solid var(--el-border-color-lighter, #e6e6e6);
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 60px;
  transition: background-color 0.3s, border-color 0.3s;
  color: var(--el-text-color-primary);
}

.logo-area {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo-icon {
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-buttons {
  display: flex;
  gap: 8px;
}
</style>

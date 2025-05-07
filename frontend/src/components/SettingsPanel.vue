<template>
  <div class="settings-tab">
    <h3 class="section-title">系统设置</h3>

    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <span>界面设置</span>
        </div>
      </template>

      <!-- 深色模式切换 -->
      <div class="setting-item">
        <span class="setting-label">深色模式</span>
        <div class="setting-control">
          <el-switch
            v-model="darkMode"
            :active-icon="Moon"
            :inactive-icon="Sunny"
            @change="toggleDarkMode"
          />
        </div>
      </div>

      <!-- 界面动画效果 -->
      <div class="setting-item">
        <span class="setting-label">界面动画效果</span>
        <div class="setting-control">
          <el-switch v-model="enableAnimations" @change="toggleAnimations" />
        </div>
      </div>
      
      <!-- 系统紧凑模式 -->
      <div class="setting-item">
        <span class="setting-label">紧凑界面</span>
        <div class="setting-control">
          <el-select v-model="density" placeholder="选择密度" style="width: 150px">
            <el-option label="默认" value="default" />
            <el-option label="紧凑" value="compact" />
          </el-select>
        </div>
      </div>
    </el-card>

    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <span>应用设置</span>
        </div>
      </template>

      <!-- 自动检查更新 -->
      <div class="setting-item">
        <span class="setting-label">自动检查更新</span>
        <div class="setting-control">
          <el-switch v-model="autoCheckUpdates" />
        </div>
      </div>

      <!-- 日志级别 -->
      <div class="setting-item">
        <span class="setting-label">日志级别</span>
        <div class="setting-control">
          <el-select v-model="logLevel" placeholder="选择日志级别" style="width: 150px">
            <el-option label="调试" value="debug" />
            <el-option label="信息" value="info" />
            <el-option label="警告" value="warn" />
            <el-option label="错误" value="error" />
          </el-select>
        </div>
      </div>
    </el-card>

    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <span>关于</span>
        </div>
      </template>

      <div class="about-content">
        <p><strong>X² Launcher</strong> - MaiBot 管理器</p>
        <p>版本: 1.0.0</p>
        <p>
          <el-button type="primary" link @click="checkForUpdates" :loading="checkingUpdates">
            检查更新
          </el-button>
        </p>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, inject } from 'vue';
import { ElMessage } from 'element-plus';
import { Moon, Sunny } from '@element-plus/icons-vue';

// 深色模式设置
const darkMode = ref(false);
const enableAnimations = ref(true);
const density = ref('default');
const autoCheckUpdates = ref(true);
const logLevel = ref('info');

const checkingUpdates = ref(false);

// 获取本地存储中的设置
onMounted(() => {
  // 加载深色模式设置
  const savedDarkMode = localStorage.getItem('darkMode');
  if (savedDarkMode !== null) {
    darkMode.value = savedDarkMode === 'true';
    applyDarkMode(darkMode.value);
  } else {
    // 检查系统偏好
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    darkMode.value = prefersDark;
    applyDarkMode(prefersDark);
  }

  // 加载其他的配置
  const savedAnimations = localStorage.getItem('enableAnimations');
  if (savedAnimations !== null) {
    enableAnimations.value = savedAnimations === 'true';
  }

  const savedDensity = localStorage.getItem('density');
  if (savedDensity) {
    density.value = savedDensity;
  }

  const savedLogLevel = localStorage.getItem('logLevel');
  if (savedLogLevel) {
    logLevel.value = savedLogLevel;
  }

  const savedAutoCheck = localStorage.getItem('autoCheckUpdates');
  if (savedAutoCheck !== null) {
    autoCheckUpdates.value = savedAutoCheck === 'true';
  }
});

// 获取事件总线
const emitter = inject('emitter', null);

// 切换深色模式
const toggleDarkMode = (value) => {
  localStorage.setItem('darkMode', value);
  applyDarkMode(value);
  
  // 通知系统深色模式已更改
  if (emitter) {
    emitter.emit('dark-mode-changed', value);
  }
};

// 应用深色模式
const applyDarkMode = (isDark) => {
  if (isDark) {
    document.documentElement.classList.add('dark-mode');
    document.documentElement.setAttribute('data-theme', 'dark');
  } else {
    document.documentElement.classList.remove('dark-mode');
    document.documentElement.setAttribute('data-theme', 'light');
  }
};

// 切换动画效果
const toggleAnimations = (value) => {
  localStorage.setItem('enableAnimations', value);
  if (!value) {
    document.documentElement.classList.add('no-animations');
  } else {
    document.documentElement.classList.remove('no-animations');
  }
};

// 监听密度变化
const watchDensity = (newValue) => {
  localStorage.setItem('density', newValue);
  document.documentElement.setAttribute('data-density', newValue);
};

// 检查更新
const checkForUpdates = async () => {
  checkingUpdates.value = true;
  
  try {
    // 模拟检查更新的过程
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    ElMessage.success('您的应用已是最新版本');
  } catch (error) {
    ElMessage.error('检查更新时出错');
    console.error('检查更新失败:', error);
  } finally {
    checkingUpdates.value = false;
  }
};

// 监听选项变化
watchDensity(density.value);
</script>

<style scoped>
.settings-tab {
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
}

.section-title {
  margin-bottom: 20px;
  color: var(--el-color-primary);
}

.settings-card {
  margin-bottom: 20px;
  transition: all 0.3s ease;
}

.settings-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.card-header {
  font-weight: bold;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.setting-item:last-child {
  border-bottom: none;
}

.setting-label {
  font-size: 14px;
}

.setting-control {
  display: flex;
  align-items: center;
}

.about-content {
  padding: 8px 0;
}

/* 深色模式样式覆盖 */
:deep(.dark-mode) .settings-card {
  background-color: var(--el-bg-color);
  color: var(--el-text-color-primary);
}
</style>

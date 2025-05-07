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

      <!-- 主题色选择 -->
      <div class="setting-item">
        <span class="setting-label">主题色</span>
        <div class="setting-control color-theme-selector">
          <div 
            v-for="(color, name) in themeColors" 
            :key="name"
            class="color-item" 
            :class="{ active: selectedTheme === name }"
            :style="{ backgroundColor: color }"
            @click="selectTheme(name, color)"
          ></div>
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
        <p>版本: 0.1.1</p>
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
import { ref, onMounted, inject, watch } from 'vue';
import { ElMessage } from 'element-plus';
import { Moon, Sunny } from '@element-plus/icons-vue';

// 获取共享状态
const emitter = inject('emitter');
const appDarkMode = inject('darkMode', ref(false)); // 使用App.vue提供的darkMode

// 设置状态
const darkMode = ref(false);
const enableAnimations = ref(true);
const density = ref('default');
const autoCheckUpdates = ref(true);
const logLevel = ref('info');

// 主题色选项
const themeColors = {
  blue: '#4a7eff',
  green: '#42b983',
  purple: '#9370db',
  orange: '#e67e22',
  pink: '#e84393',
  teal: '#00b894'
};

const selectedTheme = ref('blue'); // 默认主题色
const checkingUpdates = ref(false);

// 同步深色模式状态
watch(appDarkMode, (newValue) => {
  darkMode.value = newValue;
});

// 获取本地存储中的设置
onMounted(() => {
  // 同步深色模式设置
  darkMode.value = appDarkMode.value;

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
  
  // 加载保存的主题色
  const savedTheme = localStorage.getItem('themeColor');
  if (savedTheme && themeColors[savedTheme]) {
    selectedTheme.value = savedTheme;
    applyThemeColor(themeColors[savedTheme]);
  }
});

// 切换深色模式 - 通过事件总线通知App.vue
const toggleDarkMode = (value) => {
  localStorage.setItem('darkMode', value);
  
  // 通过事件总线通知应用
  if (emitter) {
    emitter.emit('dark-mode-changed', value);
  }
};

// 选择主题色
const selectTheme = (name, color) => {
  selectedTheme.value = name;
  localStorage.setItem('themeColor', name);
  applyThemeColor(color);
};

// 应用主题色到CSS变量
const applyThemeColor = (color) => {
  document.documentElement.style.setProperty('--el-color-primary', color);
  document.documentElement.style.setProperty('--primary-color', color);
  
  // 生成主题色的亮色和暗色变体
  const lightenColor = adjustColorBrightness(color, 20);
  const darkenColor = adjustColorBrightness(color, -20);
  
  document.documentElement.style.setProperty('--primary-light', lightenColor);
  document.documentElement.style.setProperty('--primary-dark', darkenColor);
  
  // 通知应用主题色已变更
  if (emitter) {
    emitter.emit('theme-color-changed', color);
  }
};

// 颜色亮度调整工具函数
const adjustColorBrightness = (hex, percent) => {
  // 将十六进制颜色转换为RGB
  let r = parseInt(hex.substring(1, 3), 16);
  let g = parseInt(hex.substring(3, 5), 16);
  let b = parseInt(hex.substring(5, 7), 16);

  // 调整亮度
  r = Math.min(255, Math.max(0, r + (r * percent / 100)));
  g = Math.min(255, Math.max(0, g + (g * percent / 100)));
  b = Math.min(255, Math.max(0, b + (b * percent / 100)));

  // 转回十六进制
  const rHex = Math.round(r).toString(16).padStart(2, '0');
  const gHex = Math.round(g).toString(16).padStart(2, '0');
  const bHex = Math.round(b).toString(16).padStart(2, '0');
  
  return `#${rHex}${gHex}${bHex}`;
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

<style>
@import '../assets/css/settingsPanel.css';

/* 添加设置面板的整体样式，确保不被侧边栏遮挡 */
.settings-tab {
  padding: 20px;
  box-sizing: border-box;
  width: 100%;
  overflow-y: auto;
  height: 100%;
}

/* 调整卡片样式 */
.settings-card {
  margin-bottom: 20px;
  max-width: 800px;
  transition: all 0.3s ease;
}

/* 主题色选择器样式 */
.color-theme-selector {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.color-item {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
  position: relative;
}

.color-item.active {
  border-color: var(--text-color);
}

.color-item.active::after {
  content: "✓";
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: white;
  font-weight: bold;
  font-size: 14px;
  text-shadow: 0 0 2px rgba(0, 0, 0, 0.5);
}

.color-item:hover {
  transform: scale(1.1);
  box-shadow: 0 0 10px 0 rgba(0, 0, 0, 0.2);
}
</style>

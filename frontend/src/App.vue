<template>
  <div class="app-container" :class="{ 'dark-mode': darkMode }">
    <!-- 侧边栏 -->
    <AppSidebar :is-expanded="sidebarExpanded" @toggle="toggleSidebar" />
    
    <!-- 主内容区域 -->
    <div class="content-area" :class="{ 'sidebar-expanded': sidebarExpanded }">
      <!-- 页面切换动画 -->
      <transition name="page-transition" mode="out-in">
        <component :is="currentComponent" :key="activeTab" />
      </transition>
    </div>
  </div>
</template>

<script setup>
import { ref, provide, onMounted, computed, onBeforeUnmount, watch } from 'vue'
import HomeView from './components/HomeView.vue'
import LogsPanel from './components/LogsPanel.vue'
import DownloadsPanel from './components/DownloadsPanel.vue'
import InstancesPanel from './components/InstancesPanel.vue'
import SettingsPanel from './components/SettingsPanel.vue'
import AppSidebar from './components/AppSidebar.vue'
import { HomeFilled, List, Download, Document, Setting, Grid } from '@element-plus/icons-vue'

// 深色模式状态 - 应用级别的中心管理
const darkMode = ref(false);
// 侧边栏展开状态
const sidebarExpanded = ref(false);

// 创建更完整的事件总线
const emitter = {
  _events: {},
  on(event, callback) {
    if (!this._events[event]) this._events[event] = [];
    this._events[event].push(callback);
  },
  emit(event, ...args) {
    if (this._events[event]) {
      this._events[event].forEach(callback => callback(...args));
    }
  },
  off(event, callback) {
    if (this._events[event]) {
      if (callback) {
        this._events[event] = this._events[event].filter(cb => cb !== callback);
      } else {
        // 如果没有传回调，则删除整个事件
        delete this._events[event];
      }
    }
  },
  // 添加清理方法
  clear() {
    this._events = {};
  }
};

// 提供事件总线给所有组件
provide('emitter', emitter);

// 提供深色模式状态给所有组件
provide('darkMode', darkMode);

// 提供侧边栏状态给所有组件
provide('sidebarExpanded', sidebarExpanded);

// 日志面板引用
const logsPanel = ref(null);

// 侧边栏菜单项
const menuItems = {
  home: { title: '主页', icon: HomeFilled },
  instances: { title: '实例管理', icon: List },
  downloads: { title: '下载中心', icon: Download },
  logs: { title: '系统日志', icon: Document },
  settings: { title: '系统设置', icon: Setting },
  plugins: { title: '插件广场', icon: Grid }
}

// 提供菜单项给侧边栏组件
provide('menuItems', menuItems);

// 标签页相关
const activeTab = ref('home')

// 处理标签页切换 - 将通过事件总线由HomeView的侧边栏触发
const handleTabSelect = (tab) => {
  activeTab.value = tab;
}

// 提供activeTab供侧边栏组件使用
provide('activeTab', activeTab);

// 计算当前组件
const currentComponent = computed(() => {
  switch (activeTab.value) {
    case 'home': return HomeView;
    case 'instances': return InstancesPanel;
    case 'downloads': return DownloadsPanel;
    case 'logs': return LogsPanel;
    case 'settings': return SettingsPanel;
    case 'plugins': 
      return {
        template: `<div class="tab-content">
                    <h3>插件广场</h3>
                    <p>功能正在开发中...</p>
                  </div>`
      };
    default: 
      return {
        template: `<div class="tab-content">
                    <h3>${menuItems[activeTab.value]?.title || activeTab.value}</h3>
                    <p>页面内容建设中...</p>
                  </div>`
      };
  }
});

// 监听深色模式变化
const updateDarkMode = (isDark) => {
  darkMode.value = isDark;
  
  // 应用深色模式到根文档
  if (isDark) {
    document.documentElement.classList.add('dark-mode');
    document.documentElement.setAttribute('data-theme', 'dark');
  } else {
    document.documentElement.classList.remove('dark-mode');
    document.documentElement.setAttribute('data-theme', 'light');
  }
};

// 初始化深色模式状态
const initDarkMode = () => {
  const savedDarkMode = localStorage.getItem('darkMode');
  if (savedDarkMode !== null) {
    darkMode.value = savedDarkMode === 'true';
  } else {
    // 检查系统偏好
    darkMode.value = window.matchMedia('(prefers-color-scheme: dark)').matches;
  }
  
  // 立即应用当前深色模式设置
  updateDarkMode(darkMode.value);
};

// 切换侧边栏状态
const toggleSidebar = () => {
  sidebarExpanded.value = !sidebarExpanded.value;
  localStorage.setItem('sidebarExpanded', sidebarExpanded.value);
  
  // 添加延迟以确保状态更新后再触发窗口调整
  setTimeout(() => window.dispatchEvent(new Event('resize')), 300);
};

// 监听侧边栏展开状态变化
const checkSidebarState = () => {
  sidebarExpanded.value = localStorage.getItem('sidebarExpanded') === 'true';
};

// 监听日志查看事件和页面导航
onMounted(() => {
  // 初始化深色模式 (从App.vue中集中管理)
  initDarkMode();
  
  // 初始化主题色
  initThemeColor();
  
  // 初始化侧边栏状态
  checkSidebarState();

  // 监听侧边栏状态变化
  window.addEventListener('storage', (e) => {
    if (e.key === 'sidebarExpanded') {
      checkSidebarState();
    }
  });

  // 定期检查侧边栏状态 - 改用事件监听
  window.addEventListener('sidebar-state-changed', () => {
    checkSidebarState();
  });

  // 监听显示实例日志事件
  emitter.on('show-instance-logs', (instanceName) => {
    // 切换到日志选项卡
    activeTab.value = 'logs';
    // 在下一个渲染周期，告诉日志面板显示特定实例的日志
    setTimeout(() => {
      if (logsPanel.value && logsPanel.value.changeLogSource) {
        logsPanel.value.changeLogSource(instanceName);
      }
    }, 100);
  });
  
  // 添加导航事件处理
  emitter.on('navigate-to-tab', (tabName) => {
    if (menuItems[tabName] || tabName === 'home') {
      activeTab.value = tabName;
    }
  });
  
  // 添加深色模式变化监听
  emitter.on('dark-mode-changed', updateDarkMode);

  // 添加主题色变化监听
  emitter.on('theme-color-changed', (color) => {
    console.log('Theme color changed to:', color);
    // 更新全局主题色变量
    window.currentThemeColor = color;
    
    // 更新图表颜色
    const lightenColor = adjustColorBrightness(color, 20);
    document.documentElement.style.setProperty('--chart-line', color);
    document.documentElement.style.setProperty('--chart-secondary', lightenColor);
    
    // 触发窗口的resize事件，让图表重新绘制
    window.dispatchEvent(new Event('resize'));
  });

  // 初始化反向API代理检测
  checkApiConnection();
  
  // 监听系统深色模式变化
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    // 只有当用户未明确设置时，才跟随系统变化
    if (localStorage.getItem('darkMode') === null) {
      updateDarkMode(e.matches);
    }
  });
});

// 初始化主题色
const initThemeColor = () => {
  const savedTheme = localStorage.getItem('themeColor');
  if (savedTheme) {
    const themeColors = {
      blue: '#4a7eff',
      green: '#42b983',
      purple: '#9370db',
      orange: '#e67e22',
      pink: '#e84393',
      teal: '#00b894'
    };
    
    if (themeColors[savedTheme]) {
      // 保存当前主题色到全局变量，供图表等组件使用
      window.currentThemeColor = themeColors[savedTheme];
      
      document.documentElement.style.setProperty('--el-color-primary', themeColors[savedTheme]);
      document.documentElement.style.setProperty('--primary-color', themeColors[savedTheme]);
      
      // 生成主题色的亮色和暗色变体
      const lightenColor = adjustColorBrightness(themeColors[savedTheme], 20);
      const darkenColor = adjustColorBrightness(themeColors[savedTheme], -20);
      
      document.documentElement.style.setProperty('--primary-light', lightenColor);
      document.documentElement.style.setProperty('--primary-dark', darkenColor);
      
      // 图表颜色绑定到主题色
      document.documentElement.style.setProperty('--chart-line', themeColors[savedTheme]);
      document.documentElement.style.setProperty('--chart-secondary', lightenColor);
    }
  } else {
    // 设置默认主题色到全局变量
    window.currentThemeColor = '#4a7eff';
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

// 组件卸载时清理
onBeforeUnmount(() => {
  // 清理事件总线
  emitter.clear();
  
  // 移除系统深色模式监听
  window.matchMedia('(prefers-color-scheme: dark)').removeEventListener('change', () => {});
});

// 检查API连接
const checkApiConnection = async () => {
  try {
    await fetch('/api/status', { 
      method: 'GET',
      headers: { 'Accept': 'application/json' },
      // 添加短超时，避免长时间等待
      signal: AbortSignal.timeout(2000)
    });
    console.log('API连接成功');
  } catch (error) {
    console.warn('API连接失败，可能需要启动后端服务:', error);
    // 使用模拟数据模式
    window._useMockData = true;
  }
};
</script>

<style>
@import './assets/css/app.css';

/* 添加侧边栏和内容区域的过渡样式 */
.content-area {
  transition: margin-left 0.3s ease, padding-left 0.3s ease;
  margin-left: 64px; /* 默认侧边栏收起状态下的边距 */
  width: calc(100% - 64px);
  box-sizing: border-box;
}

.content-area.sidebar-expanded {
  margin-left: 220px; /* 侧边栏展开时的边距 */
  width: calc(100% - 220px);
}

/* 统一所有动画效果 */
.page-transition-enter-active,
.page-transition-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.page-transition-enter-from,
.page-transition-leave-to {
  opacity: 0;
  transform: translateX(20px);
}
</style>
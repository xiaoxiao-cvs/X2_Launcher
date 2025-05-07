import { createApp } from 'vue'
import App from './App.vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import './assets/global.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

const app = createApp(App)

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 移除重复的初始化深色模式代码，因为这部分在App.vue中已经实现

// 初始化侧边栏状态 - 优化版，确保全局可访问
const initSidebar = () => {
  const sidebarState = localStorage.getItem('sidebarCollapsed') === 'true';
  const appRoot = document.getElementById('app');
  
  // 设置类和全局变量，确保一致性
  if (appRoot) {
    if (sidebarState) {
      appRoot.classList.add('sidebar-collapsed');
      // 添加自定义CSS变量到根元素
      document.documentElement.style.setProperty('--sidebar-width', '64px');
      document.documentElement.style.setProperty('--content-margin', '79px'); // 64px + 15px
    } else {
      appRoot.classList.remove('sidebar-collapsed');
      // 设置展开状态的值
      document.documentElement.style.setProperty('--sidebar-width', '220px');
      document.documentElement.style.setProperty('--content-margin', '235px'); // 220px + 15px
    }
  }
  
  // 提供全局访问点
  window.sidebarState = {
    collapsed: sidebarState,
    toggle: () => {
      const newState = !window.sidebarState.collapsed;
      localStorage.setItem('sidebarCollapsed', newState);
      window.sidebarState.collapsed = newState;
      
      if (newState) {
        appRoot?.classList.add('sidebar-collapsed');
        document.documentElement.style.setProperty('--sidebar-width', '64px');
        document.documentElement.style.setProperty('--content-margin', '79px');
      } else {
        appRoot?.classList.remove('sidebar-collapsed');
        document.documentElement.style.setProperty('--sidebar-width', '220px');
        document.documentElement.style.setProperty('--content-margin', '235px');
      }
      
      // 触发全局事件
      window.dispatchEvent(new CustomEvent('sidebar-state-changed', { 
        detail: { collapsed: newState } 
      }));
    }
  };
}

// 应用初始化
initSidebar()
app.use(ElementPlus)

// 错误处理
app.config.errorHandler = (err, vm, info) => {
  console.error('Vue Error:', err)
  console.error('Error Info:', info)
}

// 全局异常处理
window.addEventListener('unhandledrejection', event => {
  console.error('Unhandled Promise rejection:', event.reason)
})

// 创建一个模拟的系统指标API
const mockSystemMetrics = {
  getSystemMetrics: async () => {
    try {
      // 如果实际的electronAPI可用，使用它
      if (window.electronAPI && typeof window.electronAPI.getSystemMetrics === 'function') {
        return await window.electronAPI.getSystemMetrics();
      }
    } catch (e) {
      console.warn('原生electronAPI调用失败，使用模拟数据', e);
    }
    
    // 返回模拟数据
    return {
      cpu: { 
        usage: Math.random() * 30 + 20,
        cores: 8,
        frequency: 2400 
      },
      memory: {
        total: 16 * 1024 * 1024 * 1024,
        used: (Math.random() * 4 + 6) * 1024 * 1024 * 1024,
        free: 6 * 1024 * 1024 * 1024
      },
      network: {
        sent: Math.random() * 5000 * 1024,
        received: Math.random() * 8000 * 1024,
        sentRate: Math.random() * 300 * 1024,
        receivedRate: Math.random() * 500 * 1024
      }
    };
  }
};

// 提供全局API和服务
app.provide('electronAPI', mockSystemMetrics);
app.config.globalProperties.$electronAPI = mockSystemMetrics;

// 全局变量和方法 - 不直接修改window.electronAPI，而是使用我们的代理
if (!window.electronAPI) {
  try {
    // 尝试创建一个只读属性
    Object.defineProperty(window, 'electronAPI', {
      value: mockSystemMetrics,
      writable: false,
      configurable: true
    });
    console.log('electronAPI 接口成功模拟');
  } catch (e) {
    console.warn('无法定义 electronAPI:', e);
    // 失败的话，至少确保全局访问点
    window._electronAPI = mockSystemMetrics;
  }
}

// 添加模拟API处理
const originalFetch = window.fetch;
window.fetch = async function(resource, options) {
  // 检查是否是API请求
  if (typeof resource === 'string' && resource.startsWith('/api/') && window._useMockData) {
    console.log('拦截API请求，使用模拟数据:', resource);
    // 模拟API响应
    return mockApiResponse(resource, options);
  }
  // 否则使用原始fetch
  return originalFetch.apply(this, arguments);
};

// 模拟API响应
function mockApiResponse(url, options) {
  return new Promise(resolve => {
    // 短延迟，模拟网络
    setTimeout(() => {
      let responseData = { success: true };
      
      // 根据不同URL返回不同的模拟数据
      if (url.includes('/api/status')) {
        responseData = {
          mongodb: { status: 'running', info: '本地实例' },
          napcat: { status: 'running', info: '端口 8095' },
          nonebot: { status: 'stopped', info: '' },
          maibot: { status: 'stopped', info: '' }
        };
      } else if (url.includes('/api/instances')) {
        responseData = {
          instances: [
            { name: 'maibot-latest', status: 'running', installedAt: '2023-09-15', path: 'D:\\MaiBot\\latest' },
            { name: 'maibot-stable', status: 'stopped', installedAt: '2023-09-10', path: 'D:\\MaiBot\\stable' }
          ]
        };
      }
      
      // 返回模拟响应
      resolve({
        ok: true,
        json: () => Promise.resolve(responseData),
        text: () => Promise.resolve(JSON.stringify(responseData))
      });
    }, 300);
  });
}

// 挂载应用
app.mount('#app');
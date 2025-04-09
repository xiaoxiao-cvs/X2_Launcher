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

// 初始化深色模式
const initDarkMode = () => {
  const savedDarkMode = localStorage.getItem('darkMode')
  if (savedDarkMode === 'true') {
    document.documentElement.classList.add('dark-mode')
    document.documentElement.setAttribute('data-theme', 'dark')
  } else if (savedDarkMode === null && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    // 如果未设置偏好但系统是深色模式
    document.documentElement.classList.add('dark-mode')
    document.documentElement.setAttribute('data-theme', 'dark')
    localStorage.setItem('darkMode', 'true')
  }
}

// 应用初始化
initDarkMode()
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

app.mount('#app')
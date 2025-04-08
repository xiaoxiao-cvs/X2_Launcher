import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'

const app = createApp(App)

// 注册 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
}

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
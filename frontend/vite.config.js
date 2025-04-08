import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000, // 前端开发服务器端口
    proxy: {
      '/api': {
        target: 'http://localhost:5000', // 后端服务端口
        changeOrigin: true,
        secure: false,
      }
    }
  }
})

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// 自定义日志工具
const logger = {
  info: (msg) => console.log(`[X2-Launcher] ${msg}`),
  error: (msg) => console.error(`[X2-Launcher ERROR] ${msg}`)
};

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue({
      // 禁用Vue宏的明确导入警告
      reactivityTransform: true,
      template: {
        compilerOptions: {
          // 处理一些较旧的语法
          compatConfig: {
            MODE: 3
          }
        }
      }
    })
  ],
  server: {
    port: 3000, // 前端开发服务器端口
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000', // 后端服务端口
        changeOrigin: true,
        secure: false,
        ws: true, // 启用WebSocket代理
        // 添加错误处理
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            logger.error(`代理请求错误: ${err.message}`);
          });
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            logger.info(`正在代理请求: ${req.url}`);
          });
          proxy.on('proxyRes', (proxyRes, req, _res) => {
            logger.info(`收到代理响应: ${req.url} ${proxyRes.statusCode}`);
          });
        }
      }
    },
    // 减少不必要的HMR错误显示
    hmr: {
      overlay: false
    }
  },
  // 优化ECharts打包
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          echarts: ['echarts'],
          elementplus: ['element-plus']
        }
      }
    },
    // 添加CSS处理选项，优化样式表现
    cssCodeSplit: true,
    cssMinify: 'esbuild'
  },
  // 添加额外的解析选项以处理Vue宏
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    },
    dedupe: ['vue']
  },
  // 针对开发环境的优化
  optimizeDeps: {
    include: ['vue', 'axios', 'element-plus', 'echarts']
  },
  // 添加CSS相关配置，支持PostCSS处理
  css: {
    devSourcemap: true, // 开发环境下生成sourceMap
    preprocessorOptions: {
      scss: {
        additionalData: `
          $primary-color: var(--el-color-primary);
          $dark-bg: var(--el-bg-color);
        `
      }
    },
    // 修复PostCSS插件实现 - 防止缺少模块导致的错误
    postcss: {
      plugins: [
        // 仅使用已安装的插件
        ...((() => {
          try {
            const autoprefixer = require('autoprefixer');
            return [autoprefixer()];
          } catch (e) {
            console.warn('autoprefixer 未安装，跳过自动添加浏览器前缀');
            return [];
          }
        })())
      ]
    }
  }
})

import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import path from 'path';
import { spawn } from 'child_process';
import fs from 'fs';
import { fileURLToPath } from 'url';

// 启动后端服务
let backendProcess = null;
const logger = console;
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const shownErrors = new Set();

// 启动后端服务的函数
function startBackendServer() {
  // 检查Python可执行文件
  const pythonCommand = process.platform === 'win32' ? 'python' : 'python3';
  const backendDir = path.join(__dirname, '..', 'backend');
  const mainScript = path.join(backendDir, 'main.py');

  // 检查后端脚本是否存在
  if (!fs.existsSync(mainScript)) {
    logger.warn(`后端脚本不存在: ${mainScript}`);
    return null;
  }

  logger.info(`正在启动后端服务: ${pythonCommand} ${mainScript}`);
  
  try {
    // 启动后端进程
    const proc = spawn(pythonCommand, [mainScript], {
      stdio: 'pipe',
      env: { ...process.env, PYTHONIOENCODING: 'utf-8' },
      cwd: backendDir
    });

    // 处理后端输出
    proc.stdout.on('data', (data) => {
      logger.info(`[后端] ${data.toString().trim()}`);
    });
    
    proc.stderr.on('data', (data) => {
      logger.error(`[后端错误] ${data.toString().trim()}`);
    });

    // 处理进程退出
    proc.on('exit', (code) => {
      logger.info(`后端进程退出，退出码: ${code}`);
      backendProcess = null;
    });

    proc.on('error', (err) => {
      logger.error(`后端进程启动错误: ${err.message}`);
      backendProcess = null;
    });

    return proc;
  } catch (error) {
    logger.error(`启动后端失败: ${error.message}`);
    return null;
  }
}

// 在开发配置中启动后端
if (process.env.NODE_ENV !== 'production') {
  // 先检查是否已存在运行中的后端进程
  if (!backendProcess) {
    backendProcess = startBackendServer();
  }

  // 处理进程退出，确保后端正确关闭
  process.on('exit', () => {
    if (backendProcess) {
      backendProcess.kill();
    }
  });

  process.on('SIGINT', () => {
    if (backendProcess) {
      backendProcess.kill();
    }
    process.exit();
  });
}

const errorThrottle = 5000; // 同一错误5秒内不重复显示

export default defineConfig({
  plugins: [
    vue({
      // 禁用Vue宏的明确导入警告
      reactivityTransform: true,
      template: {
        compilerOptions: {
          compatConfig: {
            MODE: 3
          }
        }
      }
    })
  ],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000', // 后端服务端口
        changeOrigin: true,
        secure: false,
        ws: true, // 启用WebSocket代理
        // 添加错误处理
        configure: (proxy, _options) => {
          // 是否已经显示了"后端未启动"的警告
          let backendWarningShown = false;
          
          // 处理代理错误
          proxy.on('error', (err, req, _res) => {
            // 生成错误键，用于去重
            const errorKey = `${req.url}-${err.code}-${err.message}`;
            
            // 仅在一定时间内首次出现时显示
            if (!shownErrors.has(errorKey)) {
              // 如果是连接被拒绝（后端未启动），尝试启动后端
              if (err.code === 'ECONNREFUSED' && !backendWarningShown) {
                logger.warn(`后端服务未启动或不可访问 (${err.address}:${err.port})，尝试启动后端...`);
                backendWarningShown = true;
                
                // 尝试重新启动后端
                if (!backendProcess) {
                  backendProcess = startBackendServer();
                  if (backendProcess) {
                    logger.info('后端服务已启动，请等待几秒钟后重试');
                  } else {
                    logger.warn('后端服务启动失败，已切换到模拟数据模式');
                  }
                }
              } else if (err.code !== 'ECONNREFUSED') {
                // 其他错误正常显示
                logger.error(`代理请求错误: ${req.url} - ${err.message}`);
              }
              
              // 添加到已显示集合
              shownErrors.add(errorKey);
              
              // 一定时间后从集合中移除，允许再次显示
              setTimeout(() => {
                shownErrors.delete(errorKey);
              }, errorThrottle);
            }
          });
          
          // 仅在调试模式下记录请求和响应
          if (process.env.DEBUG_PROXY) {
            proxy.on('proxyReq', (_proxyReq, req, _res) => {
              logger.info(`代理请求: ${req.url}`);
            });
            
            proxy.on('proxyRes', (proxyRes, req, _res) => {
              logger.info(`代理响应: ${req.url} ${proxyRes.statusCode}`);
            });
          }
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
});

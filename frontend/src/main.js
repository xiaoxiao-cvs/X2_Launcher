import { createApp } from "vue";
import App from "./App.vue";
import ElementPlus, { ElMessage } from "element-plus";
import "element-plus/dist/index.css";
import "./assets/global.css";
import * as ElementPlusIconsVue from "@element-plus/icons-vue";
import {
  checkBackendConnection,
  startConnectionRetry,
} from "./utils/backendChecker";

// 创建应用实例
const app = createApp(App);

// =======================================
// 注册所有Element Plus图标
// =======================================
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component);
}

// =======================================
// CSS变量初始化
// =======================================
const initCssVariables = () => {
  // 获取侧边栏状态
  const sidebarCollapsed = localStorage.getItem("sidebarCollapsed") === "true";

  // 设置CSS变量
  document.documentElement.style.setProperty(
    "--sidebar-width",
    sidebarCollapsed ? "64px" : "220px"
  );
  document.documentElement.style.setProperty(
    "--content-margin",
    sidebarCollapsed ? "79px" : "235px"
  );
  document.documentElement.style.setProperty(
    "--content-width",
    sidebarCollapsed ? "calc(100% - 64px)" : "calc(100% - 220px)"
  );

  // 保存侧边栏状态到全局，供组件访问
  window.sidebarState = {
    collapsed: sidebarCollapsed,
    toggle: () => {
      const newState = !window.sidebarState.collapsed;
      localStorage.setItem("sidebarCollapsed", newState);
      window.sidebarState.collapsed = newState;

      // 更新CSS变量
      document.documentElement.style.setProperty(
        "--sidebar-width",
        newState ? "64px" : "220px"
      );
      document.documentElement.style.setProperty(
        "--content-margin",
        newState ? "79px" : "235px"
      );
      document.documentElement.style.setProperty(
        "--content-width",
        newState ? "calc(100% - 64px)" : "calc(100% - 220px)"
      );

      // 更新DOM类名并触发resize事件
      const appRoot = document.getElementById("app");
      if (appRoot) {
        if (newState) {
          appRoot.classList.add("sidebar-collapsed");
        } else {
          appRoot.classList.remove("sidebar-collapsed");
        }

        // 触发窗口resize事件，以便图表等组件可以正确调整尺寸
        setTimeout(() => {
          window.dispatchEvent(new Event("resize"));
        }, 300);
      }

      // 触发自定义事件，通知侧边栏状态变化
      window.dispatchEvent(new CustomEvent("sidebar-state-changed"));
    },
  };

  // 初始化DOM类名
  const appRoot = document.getElementById("app");
  if (appRoot) {
    if (sidebarCollapsed) {
      appRoot.classList.add("sidebar-collapsed");
    } else {
      appRoot.classList.remove("sidebar-collapsed");
    }
  }
};

// =======================================
// 系统功能模拟
// =======================================

// 创建一个性能监控API
const createPerformanceAPI = () => {
  return {
    getSystemMetrics: async () => {
      try {
        // 如果实际的electronAPI可用，使用它
        // 修复递归调用问题：确保我们不是在引用自己创建的electronAPI
        if (
          window.electronAPI &&
          typeof window.electronAPI.getSystemMetrics === "function" &&
          window.electronAPI !== window._electronAPI // 防止自引用
        ) {
          return await window.electronAPI.getSystemMetrics();
        }
      } catch (e) {
        console.warn("原生electronAPI调用失败，使用模拟数据", e);
      }

      // 返回模拟数据
      return {
        cpu: {
          usage: Math.random() * 30 + 20,
          cores: 8,
          frequency: 2400,
          model: "CPU 模拟数据",
        },
        memory: {
          total: 16 * 1024 * 1024 * 1024,
          used: (Math.random() * 4 + 6) * 1024 * 1024 * 1024,
          free: 6 * 1024 * 1024 * 1024,
        },
        network: {
          sent: Math.random() * 5000 * 1024,
          received: Math.random() * 8000 * 1024,
          sentRate: Math.random() * 300 * 1024,
          receivedRate: Math.random() * 500 * 1024,
        },
      };
    },
  };
};

// 添加API拦截器
const setupApiMock = () => {
  // 保存原始fetch方法
  const originalFetch = window.fetch;

  // 替换fetch方法，拦截API请求
  window.fetch = async function (resource, options) {
    // 检查是否是API请求且需要使用模拟数据
    if (typeof resource === "string" && resource.startsWith("/api/")) {
      // 检查我们是否应该使用模拟数据
      const useMock =
        window._useMockData ||
        window.localStorage.getItem("useMockData") === "true";

      if (useMock) {
        console.log(`[模拟] 请求: ${resource}`);
        // 模拟API响应
        return mockApiResponse(resource, options);
      }

      try {
        const response = await originalFetch.apply(this, arguments);
        return response;
      } catch (error) {
        console.warn(
          `API请求失败 (${resource}): ${error.message}，切换到模拟数据`
        );
        window._useMockData = true;
        window.localStorage.setItem("useMockData", "true");

        // 模拟API响应
        return mockApiResponse(resource, options);
      }
    }

    // 否则使用原始fetch
    return originalFetch.apply(this, arguments);
  };
};

// 模拟API响应
function mockApiResponse(url, options = {}) {
  return new Promise((resolve) => {
    // 模拟网络延迟
    setTimeout(() => {
      let responseData = { success: true };

      // 根据不同URL返回不同的模拟数据
      if (url.includes("/api/status")) {
        responseData = {
          mongodb: { status: "running", info: "本地实例 (模拟)" },
          napcat: { status: "running", info: "端口 8095 (模拟)" },
          nonebot: { status: "stopped", info: "" },
          maibot: { status: "stopped", info: "" },
        };
      } else if (url.includes("/api/instances")) {
        responseData = {
          instances: [
            {
              name: "maibot-latest",
              status: "running",
              installedAt: "2023-09-15",
              path: "D:\\MaiBot\\latest",
              services: {
                napcat: "running",
                nonebot: "stopped",
              },
            },
            {
              name: "maibot-stable",
              status: "stopped",
              installedAt: "2023-09-10",
              path: "D:\\MaiBot\\stable",
              services: {
                napcat: "stopped",
                nonebot: "stopped",
              },
            },
          ],
        };
      } else if (url.includes("/api/versions")) {
        responseData = {
          versions: ["latest", "beta", "stable", "v1.0.0", "v0.9.0"],
        };
      } else if (url.includes("/api/deploy/")) {
        responseData = {
          success: true,
          message: "模拟部署成功",
          instanceName: "maibot-simulated",
        };
      } else if (url.includes("/api/install/")) {
        responseData = {
          success: true,
          inProgress: false,
          message: "模拟安装完成",
        };
      } else if (url.includes("/api/logs/")) {
        responseData = {
          logs: [
            {
              time: "2023-09-15 12:00:00",
              level: "INFO",
              message: "这是模拟日志数据",
              source: "system",
            },
            {
              time: "2023-09-15 12:01:00",
              level: "WARNING",
              message: "您正在使用模拟数据模式",
              source: "system",
            },
            {
              time: "2023-09-15 12:02:00",
              level: "INFO",
              message: "启动后端服务可获取真实数据",
              source: "system",
            },
          ],
        };
      }

      // 处理模拟POST请求
      if (options.method === "POST") {
        if (url.includes("/api/install/configure")) {
          responseData = {
            success: true,
            message: "模拟配置已提交",
          };
        } else if (url.includes("/api/start/")) {
          responseData = {
            success: true,
            message: "模拟启动成功",
          };
        } else if (url.includes("/api/stop")) {
          responseData = {
            success: true,
            message: "模拟停止成功",
          };
        }
      }

      // 返回模拟响应
      resolve({
        ok: true,
        json: () => Promise.resolve(responseData),
        text: () => Promise.resolve(JSON.stringify(responseData)),
        status: 200,
        headers: new Headers({ "Content-Type": "application/json" }),
      });
    }, 300);
  });
}

// =======================================
// 应用初始化
// =======================================

// 初始化应用
const initApp = () => {
  // 初始化CSS变量
  initCssVariables();

  // 使用Element Plus
  app.use(ElementPlus);

  // 全局错误处理
  app.config.errorHandler = (err, vm, info) => {
    console.error("Vue错误:", err);
    console.error("错误信息:", info);
  };

  // 全局异常处理
  window.addEventListener("unhandledrejection", (event) => {
    console.error("未处理的Promise拒绝:", event.reason);
  });

  // 创建并提供性能监控API
  const performanceAPI = createPerformanceAPI();
  app.provide("electronAPI", performanceAPI);
  app.config.globalProperties.$electronAPI = performanceAPI;

  // 如果没有原生electronAPI，提供模拟版本
  if (!window.electronAPI) {
    try {
      // 修复：先创建API实例，再定义属性
      const performanceAPIInstance = createPerformanceAPI();

      // 保存一个引用到全局变量，以便检测自引用
      window._electronAPI = performanceAPIInstance;

      Object.defineProperty(window, "electronAPI", {
        value: performanceAPIInstance,
        writable: false,
        configurable: true,
      });
      console.log("electronAPI 接口成功模拟");
    } catch (e) {
      console.warn("无法定义 electronAPI:", e);
      // 备用方案
      window._electronAPI = createPerformanceAPI();
    }
  }

  // 检查API连接状态并自动重试连接
  checkInitialBackendConnection();

  // 设置API模拟
  setupApiMock();

  // 挂载应用
  app.mount("#app");
};

// 检查初始后端连接
const checkInitialBackendConnection = async () => {
  // 显示后端连接中的通知
  const loadingNotification = ElMessage({
    message: "正在连接后端服务...",
    type: "info",
    duration: 0,
    showClose: false,
  });

  try {
    const connected = await checkBackendConnection();

    // 关闭加载提示
    loadingNotification.close();

    if (connected) {
      console.log("后端服务连接成功");
      ElMessage({
        message: "后端服务连接成功",
        type: "success",
        duration: 3000,
      });
      // 连接成功后关闭模拟模式
      window._useMockData = false;
      window.localStorage.setItem("useMockData", "false");
    } else {
      console.warn("后端服务连接失败，启动自动重试");
      // 启动自动重试
      startConnectionRetry(() => {
        ElMessage({
          message: "后端服务连接成功",
          type: "success",
          duration: 3000,
        });
        // 连接成功后关闭模拟模式
        window._useMockData = false;
        window.localStorage.setItem("useMockData", "false");
      });

      // 显示友好的提示
      setTimeout(() => {
        ElMessage({
          message: "后端服务未启动，已切换到模拟数据模式，功能将受限",
          type: "warning",
          duration: 5000,
        });
      }, 500);
    }
  } catch (error) {
    // 关闭加载提示
    loadingNotification.close();

    console.error("后端连接检查失败:", error);
    // 启动自动重试
    startConnectionRetry(() => {
      ElMessage({
        message: "后端服务连接成功",
        type: "success",
        duration: 3000,
      });
      // 连接成功后关闭模拟模式
      window._useMockData = false;
      window.localStorage.setItem("useMockData", "false");
    });
  }
};

// 启动应用
initApp();

// 添加侧边栏状态同步
window.addEventListener("sidebar-state-changed", () => {
  const sidebarCollapsed = localStorage.getItem("sidebarExpanded") !== "true";

  // 更新CSS变量
  document.documentElement.style.setProperty(
    "--sidebar-width",
    sidebarCollapsed ? "64px" : "220px"
  );
  document.documentElement.style.setProperty(
    "--content-margin",
    sidebarCollapsed ? "79px" : "235px"
  );
  document.documentElement.style.setProperty(
    "--content-width",
    sidebarCollapsed ? "calc(100% - 64px)" : "calc(100% - 220px)"
  );

  console.log("侧边栏状态已同步:", sidebarCollapsed ? "折叠" : "展开");
});

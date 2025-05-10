import fetch from "node-fetch";

// 要测试的API端点
const endpoints = [
  { url: "http://localhost:5000/api/health", name: "健康检查" },
  { url: "http://localhost:5000/api/status", name: "状态API" },
  { url: "http://localhost:5000/api/instances", name: "实例列表" },
  { url: "http://localhost:5000/api/instance-stats", name: "实例统计(旧)" },
  { url: "http://localhost:5000/api/instances/stats", name: "实例统计(新)" },
];

async function checkEndpoint(endpoint) {
  try {
    console.log(`正在检查 ${endpoint.name} (${endpoint.url})...`);
    const start = Date.now();
    const response = await fetch(endpoint.url, { timeout: 5000 });
    const time = Date.now() - start;

    if (response.ok) {
      console.log(`✅ ${endpoint.name}: 状态码 ${response.status} (${time}ms)`);
      const data = await response.json();
      console.log(`   数据: ${JSON.stringify(data)}`);
      return true;
    } else {
      console.log(`❌ ${endpoint.name}: 状态码 ${response.status} (${time}ms)`);
      return false;
    }
  } catch (error) {
    console.log(`❌ ${endpoint.name}: ${error.message}`);
    return false;
  }
}

async function main() {
  console.log("===== API可用性检查 =====");

  let successCount = 0;
  for (const endpoint of endpoints) {
    const success = await checkEndpoint(endpoint);
    if (success) successCount++;
  }

  console.log("=======================");
  console.log(`结果: ${successCount}/${endpoints.length} 个端点可用`);

  if (successCount < endpoints.length) {
    console.log("\n可能的解决方案:");
    console.log("1. 确保后端服务正在运行 (python backend/main.py)");
    console.log("2. 检查端口 5000 是否被其他程序占用");
    console.log("3. 查看后端日志以获取更多信息");
  }
}

main().catch(console.error);

/**
 * API检测脚本 - 在构建过程中检查API连接
 */
const http = require("http");
const https = require("https");
const fs = require("fs");
const path = require("path");

// 配置
const API_URL = "http://localhost:5000/api/health";
const TIMEOUT = 5000;
const MAX_RETRIES = 3;
const RETRY_DELAY = 2000;

// 颜色工具函数
const colors = {
  reset: "\x1b[0m",
  bright: "\x1b[1m",
  red: "\x1b[31m",
  green: "\x1b[32m",
  yellow: "\x1b[33m",
  blue: "\x1b[34m",
};

console.log(
  `${colors.bright}${colors.blue}===== API 连接检测 =====${colors.reset}\n`
);

/**
 * 检查API连接
 * @param {string} url - API URL
 * @param {number} retryCount - 当前尝试次数
 * @returns {Promise<boolean>} - API是否可用
 */
function checkApiConnection(url, retryCount = 0) {
  return new Promise((resolve) => {
    console.log(
      `${colors.yellow}尝试连接API: ${url} (尝试 ${
        retryCount + 1
      }/${MAX_RETRIES})${colors.reset}`
    );

    const client = url.startsWith("https") ? https : http;
    const req = client.get(url, { timeout: TIMEOUT }, (res) => {
      let data = "";

      res.on("data", (chunk) => {
        data += chunk;
      });

      res.on("end", () => {
        if (res.statusCode === 200) {
          try {
            const response = JSON.parse(data);
            console.log(
              `${colors.green}√ API连接成功: ${JSON.stringify(response)}${
                colors.reset
              }`
            );
            resolve(true);
          } catch (e) {
            console.log(
              `${colors.red}× API响应解析失败: ${e.message}${colors.reset}`
            );
            retryOrResolve(url, retryCount, resolve);
          }
        } else {
          console.log(
            `${colors.red}× API响应状态码异常: ${res.statusCode}${colors.reset}`
          );
          retryOrResolve(url, retryCount, resolve);
        }
      });
    });

    req.on("error", (err) => {
      console.log(`${colors.red}× API连接错误: ${err.message}${colors.reset}`);
      retryOrResolve(url, retryCount, resolve);
    });

    req.on("timeout", () => {
      console.log(`${colors.red}× API连接超时${colors.reset}`);
      req.abort();
      retryOrResolve(url, retryCount, resolve);
    });
  });
}

/**
 * 重试连接或返回结果
 * @param {string} url - API URL
 * @param {number} retryCount - 当前尝试次数
 * @param {function} resolve - Promise的resolve函数
 */
function retryOrResolve(url, retryCount, resolve) {
  if (retryCount < MAX_RETRIES - 1) {
    console.log(
      `${colors.yellow}将在 ${RETRY_DELAY / 1000} 秒后重试...${colors.reset}`
    );
    setTimeout(() => {
      checkApiConnection(url, retryCount + 1).then(resolve);
    }, RETRY_DELAY);
  } else {
    console.log(`${colors.red}达到最大重试次数，API可能不可用${colors.reset}`);
    resolve(false);
  }
}

/**
 * 主函数
 */
async function main() {
  const isApiAvailable = await checkApiConnection(API_URL);

  console.log(
    `\n${colors.bright}${colors.blue}===== 检测结果 =====${colors.reset}`
  );
  if (isApiAvailable) {
    console.log(
      `${colors.green}API服务可用，你可以正常使用X2 Launcher${colors.reset}`
    );
    process.exit(0);
  } else {
    console.log(
      `${colors.yellow}API服务不可用，前端可能会使用模拟数据模式${colors.reset}`
    );
    console.log(
      `${colors.yellow}你可以尝试先启动后端服务: python backend/main.py${colors.reset}`
    );
    // 我们不因此退出失败，只是提示用户
    process.exit(0);
  }
}

// 执行主函数
main().catch((err) => {
  console.error(
    `${colors.red}运行检测脚本时发生错误: ${err.message}${colors.reset}`
  );
  process.exit(1);
});

import axios from 'axios';
import { exec } from 'child_process';
import fs from 'fs';
import path from 'path';
import os from 'os';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// 颜色输出
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
  white: '\x1b[37m',
};

async function checkService(url) {
  try {
    const response = await axios.get(url, { timeout: 3000 });
    return {
      available: true,
      status: response.status,
      data: response.data
    };
  } catch (error) {
    return {
      available: false,
      error: error.message,
      code: error.code,
    };
  }
}

function checkProcess(processName) {
  return new Promise((resolve) => {
    const cmd = process.platform === 'win32'
      ? `tasklist /FI "IMAGENAME eq ${processName}" /FO CSV`
      : `ps -ef | grep ${processName} | grep -v grep`;
    
    exec(cmd, (error, stdout) => {
      if (error || !stdout.trim()) {
        resolve({ running: false });
      } else {
        resolve({ 
          running: true,
          output: stdout.trim()
        });
      }
    });
  });
}

function printResult(name, result, successMessage, failMessage) {
  if (result.available || result.running) {
    console.log(`${colors.green}✓${colors.reset} ${name}: ${successMessage}`);
  } else {
    console.log(`${colors.red}✗${colors.reset} ${name}: ${failMessage}`);
    if (result.error) {
      console.log(`  ${colors.yellow}错误:${colors.reset} ${result.error}`);
    }
    if (result.code) {
      console.log(`  ${colors.yellow}代码:${colors.reset} ${result.code}`);
    }
    if (result.output) {
      console.log(`  ${colors.yellow}输出:${colors.reset} ${result.output}`);
    }
  }
}

async function main() {
  console.log(`${colors.cyan}==== X2 Launcher 诊断工具 ====${colors.reset}`);
  console.log(`运行时间: ${new Date().toLocaleString()}`);
  console.log(`操作系统: ${os.platform()} ${os.release()} (${os.arch()})`);
  console.log(`Node.js: ${process.version}`);
  console.log("");
  
  // 检查后端服务
  console.log(`${colors.magenta}检查后端服务:${colors.reset}`);
  const healthResult = await checkService('http://localhost:5000/api/health');
  printResult('健康检查API', healthResult, '可访问', '不可访问');
  
  const instancesResult = await checkService('http://localhost:5000/api/instances');
  printResult('实例列表API', instancesResult, '可访问', '不可访问');
  
  const statsResult = await checkService('http://localhost:5000/api/instances/stats');
  printResult('实例统计API', statsResult, '可访问', '不可访问');
  
  // 检查进程
  console.log(`\n${colors.magenta}检查进程:${colors.reset}`);
  const pythonProcess = await checkProcess('python.exe');
  printResult('Python进程', pythonProcess, '正在运行', '未运行');
  
  const electronProcess = await checkProcess('electron.exe');
  printResult('Electron进程', electronProcess, '正在运行', '未运行');
  
  // 检查文件
  console.log(`\n${colors.magenta}检查关键文件:${colors.reset}`);
  const rootDir = path.resolve(__dirname, '..');
  const files = [
    { path: path.join(rootDir, 'backend', 'main.py'), name: 'Backend main.py' },
    { path: path.join(rootDir, 'frontend', 'vite.config.js'), name: 'Vite config' },
    { path: path.join(rootDir, 'frontend', 'src', 'api', 'instances.js'), name: 'Instances API' }
  ];
  
  for (const file of files) {
    const exists = fs.existsSync(file.path);
    printResult(file.name, { available: exists }, '存在', '不存在');
    if (exists) {
      const stats = fs.statSync(file.path);
      console.log(`  上次修改: ${stats.mtime.toLocaleString()}`);
    }
  }
  
  // 建议
  console.log(`\n${colors.magenta}诊断建议:${colors.reset}`);
  if (!healthResult.available) {
    console.log(`${colors.yellow}• 后端服务不可访问，请检查是否已启动${colors.reset}`);
    console.log(`  尝试运行: cd backend && python main.py`);
  }
  
  if (healthResult.available && (!instancesResult.available || !statsResult.available)) {
    console.log(`${colors.yellow}• API端点不可用，请检查路由配置${colors.reset}`);
    console.log(`  查看 backend/routes/api.py 文件中的路由定义`);
  }
  
  console.log(`\n${colors.cyan}==== 诊断结束 ====${colors.reset}`);
}

main().catch(console.error);

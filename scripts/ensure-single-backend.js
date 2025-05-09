import { execSync, spawn } from 'child_process';
import path from 'path';
import fs from 'fs';
import os from 'os';
import { fileURLToPath } from 'url';

// 获取当前文件的目录路径（ES模块中没有__dirname）
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// 获取平台特定的命令
const isWindows = process.platform === 'win32';
const pythonCmd = isWindows ? 'python' : 'python3';
const killCmd = isWindows ? 'taskkill /F /PID' : 'kill -9';
const findProcessCmd = isWindows ? 'tasklist /FI "IMAGENAME eq python.exe" /FO CSV' : 'ps -ef | grep python';

// 记录文件位置
const pidFile = path.join(os.tmpdir(), 'x2-launcher-backend.pid');

/**
 * 停止现有的后端进程
 */
export function stopExistingBackend() {
  try {
    // 检查PID文件
    if (fs.existsSync(pidFile)) {
      const pid = fs.readFileSync(pidFile, 'utf8').trim();
      if (pid && parseInt(pid) > 0) {
        console.log(`尝试停止后端进程 PID: ${pid}`);
        try {
          execSync(`${killCmd} ${pid}`);
          console.log(`已停止后端进程 PID: ${pid}`);
        } catch (e) {
          console.log(`停止进程失败，可能已经退出: ${e.message}`);
        }
      }
      fs.unlinkSync(pidFile);
    }
    
    // 查找可能的遗留Python进程
    console.log('检查可能的遗留Python进程...');
    const output = execSync(findProcessCmd, { encoding: 'utf8' });
    const mainPyPattern = /[Xx]2_[Ll]auncher[\/\\]backend[\/\\]main\.py/;
    
    output.split('\n').forEach(line => {
      if (mainPyPattern.test(line)) {
        const pidMatch = line.match(/\b(\d+)\b/);
        if (pidMatch && pidMatch[1]) {
          const orphanPid = pidMatch[1];
          console.log(`发现孤立的后端进程 PID: ${orphanPid}`);
          try {
            execSync(`${killCmd} ${orphanPid}`);
            console.log(`已终止孤立进程 PID: ${orphanPid}`);
          } catch (e) {
            console.log(`终止进程失败: ${e.message}`);
          }
        }
      }
    });
  } catch (err) {
    console.error('停止现有后端进程时出错:', err);
  }
}

/**
 * 启动后端进程
 */
export function startBackend() {
  const backendDir = path.resolve(__dirname, '..', 'backend');
  const mainScript = path.join(backendDir, 'main.py');
  
  if (!fs.existsSync(mainScript)) {
    console.error(`后端脚本不存在: ${mainScript}`);
    return null;
  }
  
  console.log(`启动后端: ${pythonCmd} ${mainScript}`);
  
  try {
    // 使用spawn启动后端进程
    const proc = spawn(pythonCmd, [mainScript], {
      stdio: 'pipe',
      cwd: backendDir,
      env: { ...process.env, PYTHONIOENCODING: 'utf-8' }
    });
    
    // 记录PID
    fs.writeFileSync(pidFile, proc.pid.toString());
    console.log(`后端进程已启动，PID: ${proc.pid}`);
    
    // 处理后端输出
    proc.stdout.on('data', (data) => {
      console.log(`[后端] ${data.toString().trim()}`);
    });
    
    proc.stderr.on('data', (data) => {
      console.error(`[后端错误] ${data.toString().trim()}`);
    });
    
    proc.on('exit', (code) => {
      console.log(`后端进程退出，退出码: ${code}`);
      try {
        fs.unlinkSync(pidFile);
      } catch (e) {}
    });
    
    return proc;
  } catch (error) {
    console.error(`启动后端失败: ${error.message}`);
    return null;
  }
}

// 主函数
function main() {
  console.log('确保只有一个后端进程在运行...');
  stopExistingBackend();
  return startBackend();
}

// 如果直接运行脚本，执行主函数
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

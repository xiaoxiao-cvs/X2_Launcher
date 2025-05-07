const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// 颜色工具函数
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m'
};

console.log(`${colors.bright}${colors.blue}===== X2 Launcher 开发依赖安装工具 =====${colors.reset}\n`);

// 需要安装的依赖
const dependencies = [
  'autoprefixer',
  'postcss-preset-env'
];

console.log(`${colors.yellow}开始安装缺失的依赖项...${colors.reset}`);

// 确保脚本目录存在
const scriptsDir = path.join(__dirname);
if (!fs.existsSync(scriptsDir)) {
  fs.mkdirSync(scriptsDir, { recursive: true });
}

// 安装依赖
dependencies.forEach(dep => {
  try {
    console.log(`\n${colors.blue}> 正在检查 ${dep}...${colors.reset}`);
    
    // 检查依赖是否已安装
    try {
      require(dep);
      console.log(`${colors.green}√ ${dep} 已安装${colors.reset}`);
    } catch (e) {
      console.log(`${colors.yellow}! ${dep} 未安装，正在安装...${colors.reset}`);
      
      // 安装依赖
      execSync(`npm install --save-dev ${dep}`, {
        stdio: 'inherit',
        cwd: path.join(__dirname, '..')
      });
      
      console.log(`${colors.green}√ ${dep} 安装成功${colors.reset}`);
    }
  } catch (error) {
    console.error(`${colors.red}× 安装 ${dep} 失败：${error.message}${colors.reset}`);
  }
});

console.log(`\n${colors.green}${colors.bright}===== 依赖安装结束 =====${colors.reset}`);
console.log(`${colors.blue}请重新启动开发服务器${colors.reset}`);

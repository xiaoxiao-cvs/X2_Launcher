import fetch from 'node-fetch';

// 要测试的API端点
const endpoints = [
  { url: 'http://localhost:5000/api/health', name: '健康检查' },
  { url: 'http://localhost:5000/api/status', name: '状态API' },
  { url: 'http://localhost:5000/api/instances', name: '实例列表' },
  { url: 'http://localhost:5000/api/instance-stats', name: '实例统计(旧)' },
  { url: 'http://localhost:5000/api/instances/stats', name: '实例统计(新)' }
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
  console.log('===== API可用性检查 =====');
  
  let successCount = 0;
  for (const endpoint of endpoints) {
    const success = await checkEndpoint(endpoint);
    if (success) successCount++;
  }
  
  console.log('=======================');
  console.log(`结果: ${successCount}/${endpoints.length} 个端点可用`);
  
  if (successCount < endpoints.length) {
    console.log('\n可能的解决方案:');
    console.log('1. 确保后端服务正在运行 (python backend/main.py)');
    console.log('2. 检查端口 5000 是否被其他程序占用');
    console.log('3. 查看后端日志以获取更多信息');
  }
}

main().catch(console.error);

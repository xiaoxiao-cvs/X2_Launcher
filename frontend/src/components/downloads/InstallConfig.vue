<template>
  <div class="section">
    <div class="section-title">安装Bot实例</div>
    <div class="install-container">
      <el-select 
        v-model="selectedVersion" 
        placeholder="选择版本" 
        size="default"
        :loading="versionsLoading">
        <el-option
          v-for="version in availableVersions"
          :key="version"
          :label="version"
          :value="version"
        />
      </el-select>
      <el-button 
        type="primary" 
        @click="installVersion" 
        :loading="installLoading"
        :disabled="!selectedVersion"
        size="default">
        <el-icon><Download /></el-icon> 安装
      </el-button>
    </div>
    <p v-if="versionError" class="error-message">{{ versionError }}</p>
    <p v-if="availableVersions.length === 0 && !versionsLoading" class="repo-info">
      从 <a href="https://github.com/MaiM-with-u/MaiBot" target="_blank">MaiBot 仓库</a> 获取版本
    </p>
    
    <!-- Bot配置选项 -->
    <div class="bot-config" v-if="selectedVersion">
      <el-divider content-position="left">Bot 配置</el-divider>
      
      <div class="config-options">
        <div class="option-item">
          <el-checkbox v-model="installNapcat">
            <div class="option-title">安装 NapCat</div>
            <div class="option-desc">安装 NapCat 作为机器人连接器</div>
          </el-checkbox>
        </div>
        
        <div class="option-item">
          <el-checkbox v-model="installNonebot">
            <div class="option-title">配置 NoneBot</div>
            <div class="option-desc">配置 NoneBot 机器人环境</div>
          </el-checkbox>
        </div>
        
        <div class="option-item">
          <el-checkbox v-model="runInstallScript">
            <div class="option-title">运行安装脚本</div>
            <div class="option-desc">执行Python环境配置和依赖安装</div>
          </el-checkbox>
        </div>
        
        <!-- 添加新选项：安装适配器 -->
        <div class="option-item">
          <el-checkbox v-model="installAdapter">
            <div class="option-title">安装NB适配器</div>
            <div class="option-desc">安装MaiBot的NoneBot适配器</div>
          </el-checkbox>
        </div>
      </div>
      
      <!-- QQ号输入 -->
      <div class="qq-input" v-if="installNapcat || installNonebot">
        <el-input
          v-model="qqNumber"
          placeholder="请输入QQ号"
          :prefix-icon="User"
          clearable>
          <template #prepend>QQ号</template>
        </el-input>
        <p class="input-tip">用于配置机器人连接的QQ账号</p>
      </div>
      
      <!-- 端口配置 -->
      <div class="ports-config" v-if="installNapcat || installNonebot">
        <el-divider content-position="left">端口配置</el-divider>
        <div class="ports-grid">
          <div class="port-item">
            <el-input
              v-model="noncatPort"
              type="number"
              placeholder="Napcat端口">
              <template #prepend>Napcat端口</template>
            </el-input>
            <p class="port-desc">NapCat的WebSocket服务器端口</p>
          </div>
          
          <div class="port-item">
            <el-input
              v-model="nonebotPort"
              type="number"
              placeholder="NoneBot端口">
              <template #prepend>NoneBot端口</template>
            </el-input>
            <p class="port-desc">NoneBot适配器监听端口</p>
          </div>
          
          <div class="port-item">
            <el-input
              v-model="maibotPort"
              type="number"
              placeholder="MaiBot端口">
              <template #prepend>MaiBot端口</template>
            </el-input>
            <p class="port-desc">MaiBot主程序监听端口</p>
          </div>
        </div>
      </div>
      
      <!-- 安装提示 -->
      <div class="install-tips" v-if="selectedVersion">
        <el-alert
          title="安装提示"
          type="info"
          description="安装完成后，请在实例管理中按照正确顺序启动各组件：1.NapCat 2.NoneBot 3.MaiBot"
          :closable="false"
          show-icon>
        </el-alert>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, defineProps, defineEmits, onUnmounted, inject } from 'vue';
import { ElMessage } from 'element-plus';
import { Download, User } from '@element-plus/icons-vue';
import axios from 'axios';

const props = defineProps({
  logCallback: Function
});

const emit = defineEmits(['refresh-instances', 'add-log']);

// 实例安装状态变量
const selectedVersion = ref('');
const availableVersions = ref([]);
const versionsLoading = ref(false);
const installLoading = ref(false);
const versionError = ref('');
const installStatus = ref('idle');  // idle, installing, completed, failed

// Bot配置选项
const installNapcat = ref(true);
const installNonebot = ref(true);
const runInstallScript = ref(true);  // 默认勾选运行安装脚本
const installAdapter = ref(true);    // 默认勾选安装适配器
const qqNumber = ref('');

// 端口配置
const noncatPort = ref('8095');     // NapCat默认端口
const nonebotPort = ref('18002');   // NoneBot默认端口
const maibotPort = ref('8000');     // MaiBot默认端口

// 是否可以安装Bot
const canConfigureBot = computed(() => {
  if (!installNapcat.value && !installNonebot.value) return true;
  return qqNumber.value.trim() !== '' && /^\d+$/.test(qqNumber.value);
});

// 版本安装方法
const fetchVersions = async () => {
  versionsLoading.value = true;
  versionError.value = '';
  try {
    // 添加重试和错误恢复机制
    let retryCount = 0;
    const maxRetries = 2;
    let success = false;
    
    while (!success && retryCount <= maxRetries) {
      try {
        const response = await axios.get('/api/versions', {
          // 增加超时
          timeout: 10000,
          // 添加参数以使用缓存版本
          params: {
            useCache: retryCount > 0 ? 'true' : 'false',
            fallback: retryCount > 0 ? 'true' : 'false'
          }
        });

        if (response.data && response.data.versions && response.data.versions.length > 0 && 
            !(response.data.versions.length === 1 && response.data.versions[0] === 'NaN')) {
          availableVersions.value = response.data.versions;
          success = true;
          
          if (response.data.fromCache) {
            console.log('使用缓存版本列表');
          }
          
          // 如果是使用备选版本
          if (response.data.isLocalFallback) {
            addLog({
              time: formatTime(new Date()),
              source: 'system',
              level: 'WARNING',
              message: '使用本地备用版本列表，可能不是最新版本'
            });
          }
        } else {
          throw new Error('无效的版本数据');
        }
      } catch (error) {
        retryCount++;
        if (retryCount > maxRetries) {
          throw error;
        }
        // 重试前等待
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }
  } catch (error) {
    console.error('获取版本列表失败:', error);
    
    // 在获取版本失败时提供静态版本选择
    availableVersions.value = ['latest', 'beta', 'stable', 'v1.0.0', 'v0.9.0'];
    versionError.value = '从GitHub获取版本列表失败，可能是API速率限制或网络问题。已提供备选版本选择。';

    addLog({
      time: formatTime(new Date()),
      source: 'system',
      level: 'ERROR',
      message: `版本获取失败: ${error.message || '未知错误'}`
    });
  } finally {
    versionsLoading.value = false;
  }
};

const installVersion = async () => {
  if (!selectedVersion.value) {
    ElMessage.warning('请先选择版本');
    return;
  }
  
  // 检查Bot配置
  if ((installNapcat.value || installNonebot.value) && !canConfigureBot.value) {
    ElMessage.warning('请输入有效的QQ号');
    return;
  }
  
  // 检查端口有效性
  if (!isPortValid()) {
    return;
  }
  
  installLoading.value = true;
  installStatus.value = 'installing';
  
  try {
    // 显示安装开始日志 - 使用命令行格式
    addLog({
      time: formatTime(new Date()),
      source: 'command',
      level: 'INFO',
      message: `$ 开始安装 ${selectedVersion.value}...`
    });
    
    // 1. 首先安装MaiBot实例
    const response = await axios.post(`/api/deploy/${selectedVersion.value}`);
    
    if (!response.data.success) {
      ElMessage.error(response.data.message || '安装失败');
      installStatus.value = 'failed';
      addLog({
        time: formatTime(new Date()),
        source: 'command',
        level: 'ERROR',
        message: `$ 无法安装 ${selectedVersion.value}: ${response.data.message || '未知错误'}`
      });
      installLoading.value = false;
      return;
    }
    
    addLog({
      time: formatTime(new Date()),
      source: 'command',
      level: 'SUCCESS',
      message: `$ ${selectedVersion.value} 基础安装完成`
    });
    
    // 2. 然后配置NapCat和NoneBot (如果启用)
    if (installNapcat.value || installNonebot.value || runInstallScript.value || installAdapter.value) {
      // 添加命令行指示符
      addLog({
        time: formatTime(new Date()),
        source: 'command',
        level: 'INFO',
        message: `$ 正在开始配置Bot环境...`
      });
      
      // 如果启用了各组件，显示对应的安装指示
      if (installNapcat.value) {
        addLog({
          time: formatTime(new Date()),
          source: 'command',
          level: 'INFO',
          message: `$ 配置 NapCat (QQ: ${qqNumber.value || '未指定'}, 端口: ${noncatPort.value})...`
        });
      }
      
      if (installNonebot.value) {
        addLog({
          time: formatTime(new Date()),
          source: 'command',
          level: 'INFO',
          message: `$ 配置 NoneBot (端口: ${nonebotPort.value})...`
        });
      }
      
      if (installAdapter.value) {
        addLog({
          time: formatTime(new Date()),
          source: 'command',
          level: 'INFO', 
          message: `$ 安装 NoneBot 适配器...`
        });
      }
      
      if (runInstallScript.value) {
        addLog({
          time: formatTime(new Date()),
          source: 'command',
          level: 'INFO',
          message: `$ 准备执行 Python 依赖安装...`
        });
      }
      
      // 开始进行配置并安装
      const configResponse = await axios.post('/api/install/configure', {
        qq_number: qqNumber.value,
        install_napcat: installNapcat.value,
        install_nonebot: installNonebot.value,
        run_install_script: runInstallScript.value,
        install_adapter: installAdapter.value,
        ports: {
          napcat: parseInt(noncatPort.value),
          nonebot: parseInt(nonebotPort.value),
          maibot: parseInt(maibotPort.value)
        }
      });
      
      if (configResponse.data.success) {
        addLog({
          time: formatTime(new Date()),
          source: 'command',
          level: 'SUCCESS',
          message: '$ Bot配置已提交，请等待后台安装过程完成...'
        });
      } else {
        addLog({
          time: formatTime(new Date()),
          source: 'command',
          level: 'WARNING',
          message: `$ Bot配置部分失败: ${configResponse.data.message || '未知原因'}`
        });
      }
      
      // 启动安装状态检测
      startInstallStatusPolling();
    } else {
      // 如果没有额外配置，直接刷新实例列表
      refreshInstances();
      installLoading.value = false;
    }
    
    // 通知更新实例列表
    emit('refresh-instances');
    
    ElMessage({
      message: '实例已安装，后台配置进程已启动，请查看日志了解安装进度',
      type: 'success',
      duration: 5000
    });
    
    installStatus.value = 'completed';
  } catch (error) {
    console.error('版本安装失败:', error);
    installStatus.value = 'failed';
    addLog({
      time: formatTime(new Date()),
      source: 'command',
      level: 'ERROR',
      message: `$ 安装失败: ${error.response?.data?.detail || error.message}`
    });
    ElMessage.error('安装失败: ' + (error.response?.data?.detail || error.message));
    installLoading.value = false;
  }
};

// 端口验证
const isPortValid = () => {
  // 检查端口是否在有效范围内
  const ports = [
    { name: 'NapCat', value: noncatPort.value },
    { name: 'NoneBot', value: nonebotPort.value },
    { name: 'MaiBot', value: maibotPort.value }
  ];
  
  for (const port of ports) {
    const portNum = parseInt(port.value);
    if (isNaN(portNum) || portNum < 1024 || portNum > 65535) {
      ElMessage.error(`${port.name}端口无效，请输入1024-65535之间的数字`);
      return false;
    }
  }
  
  // 检查端口是否冲突
  const portSet = new Set();
  for (const port of ports) {
    if (portSet.has(port.value)) {
      ElMessage.error(`端口冲突: ${port.name}端口与其他端口重复`);
      return false;
    }
    portSet.add(port.value);
  }
  
  return true;
};

// 添加安装状态轮询
let statusPollingInterval = null;

const startInstallStatusPolling = () => {
  // 清除已有的轮询
  if (statusPollingInterval) {
    clearInterval(statusPollingInterval);
  }
  
  // 开始新的轮询
  let checkCount = 0;
  statusPollingInterval = setInterval(async () => {
    try {
      const response = await checkInstallStatus();
      const isStillInstalling = response.napcat_installing || response.nonebot_installing;
      
      checkCount++;
      
      // 如果不再安装中或者检查次数超过60次(10分钟)，停止轮询
      if (!isStillInstalling || checkCount > 60) {
        clearInterval(statusPollingInterval);
        statusPollingInterval = null;
        
        // 恢复按钮状态
        installLoading.value = false;
        
        // 刷新实例列表
        refreshInstances();
        
        // 添加日志提示安装结束
        if (checkCount > 60) {
          addLog({
            time: formatTime(new Date()),
            source: 'command',
            level: 'WARNING',
            message: '$ 安装状态检测超时，请确认安装是否完成'
          });
        } else {
          addLog({
            time: formatTime(new Date()),
            source: 'command',
            level: 'SUCCESS',
            message: '$ 安装和配置过程已完成，请在实例管理中查看'
          });
          
          // 显示完成通知
          ElMessage({
            message: '安装和配置已全部完成，请在实例管理中查看',
            type: 'success',
            duration: 7000
          });
        }
      }
    } catch (error) {
      console.error('检查安装状态失败:', error);
    }
  }, 10000); // 每10秒检查一次
};

// 刷新实例列表辅助方法
const refreshInstances = () => {
  emit('refresh-instances');
  if (emitter) {
    emitter.emit('refresh-instances');
  }
};

// 添加emitter依赖注入
const emitter = inject('emitter', null);

// 检查安装状态API查询接口
const checkInstallStatus = async () => {
  try {
    const response = await axios.get('/api/install/status');
    return response.data;
  } catch (error) {
    console.error('获取安装状态失败:', error);
    return { napcat_installing: false, nonebot_installing: false };
  }
};

// 生命周期清理
onUnmounted(() => {
  if (statusPollingInterval) {
    clearInterval(statusPollingInterval);
  }
});

// 监听版本变化，重置配置
watch(selectedVersion, () => {
  if (selectedVersion.value) {
    installNapcat.value = true;
    installNonebot.value = true;
    runInstallScript.value = true;
    installAdapter.value = true;
    qqNumber.value = '';
    noncatPort.value = '8095';
    nonebotPort.value = '18002';
    maibotPort.value = '8000';
  }
});

// 添加日志的方法
const addLog = (log) => {
  emit('add-log', log);
};

// 格式化时间展示
function formatTime(date) {
  return date.toLocaleString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit', 
    second: '2-digit'
  });
}

// 初始加载版本
fetchVersions();

// 暴露方法，供父组件调用
defineExpose({
  fetchVersions
});
</script>

<style scoped>
.install-container {
  display: flex;
  gap: 12px;
  align-items: center;
}

.error-message {
  color: #F56C6C;
  margin-top: 8px;
  font-size: 13px;
}

.repo-info {
  margin-top: 8px;
  font-size: 13px;
  color: #909399;
}

.repo-info a {
  color: var(--el-color-primary);
  text-decoration: none;
}

.repo-info a:hover {
  text-decoration: underline;
}

/* Bot配置样式 */
.bot-config {
  margin-top: 20px;
}

.config-options {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 16px;
}

.option-item {
  flex: 1;
  background: white;
  padding: 12px;
  border-radius: 6px;
  border: 1px solid #ebeef5;
  transition: all 0.3s;
}

.option-item:hover {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.option-title {
  font-weight: bold;
  margin-bottom: 4px;
}

.option-desc {
  font-size: 12px;
  color: #909399;
}

.qq-input {
  margin-bottom: 16px;
}

.input-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.ports-config {
  margin-top: 16px;
}

.ports-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.port-item {
  flex: 1;
}

.port-desc {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.install-tips {
  margin-top: 16px;
}

@media (max-width: 768px) {
  .install-container, .config-options {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>

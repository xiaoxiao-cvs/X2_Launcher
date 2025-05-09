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
    
    <!-- 实例配置选项 - 添加动画效果 -->
    <transition name="config-fade">
      <div class="bot-config" v-if="selectedVersion">
        <el-divider content-position="left">实例配置</el-divider>
        
        <!-- 添加实例名称输入框 -->
        <div class="instance-name-input">
          <el-form :model="form" label-position="top">
            <el-form-item label="实例名称" required>
              <el-input 
                v-model="instanceName" 
                placeholder="请输入实例名称"
                :maxlength="50"
                show-word-limit>
              </el-input>
              <p class="input-tip">该名称将用于区分不同的Bot实例</p>
            </el-form-item>
          </el-form>
        </div>
        
        <!-- 调整复选框顺序: 先适配器，后NapCat -->
        <div class="config-options">
          <div class="option-item">
            <el-checkbox v-model="installAdapter">
              <div class="option-title">安装 NapCat 适配器</div>
              <div class="option-desc">安装 MaiBot 的 NapCat 适配器</div>
            </el-checkbox>
          </div>
          
          <div class="option-item">
            <el-checkbox v-model="installNapcat">
              <div class="option-title">安装 NapCat</div>
              <div class="option-desc">安装 NapCat 作为机器人连接器</div>
            </el-checkbox>
          </div>
        </div>
        
        <!-- QQ号输入 -->
        <div class="qq-input" v-if="installNapcat || installAdapter">
          <el-input
            v-model="qqNumber"
            placeholder="请输入QQ号"
            :prefix-icon="User"
            clearable>
            <template #prepend>QQ号</template>
          </el-input>
          <p class="input-tip">用于配置机器人连接的QQ账号</p>
        </div>
        
        <!-- 端口配置：调整为MaiBot、适配器、NapCat的顺序 -->
        <div class="ports-config" v-if="installNapcat || installAdapter">
          <el-divider content-position="left">端口配置</el-divider>
          <div class="ports-grid">
            <div class="port-item">
              <el-input
                v-model="maibotPort"
                type="number"
                placeholder="MaiBot端口">
                <template #prepend>MaiBot端口</template>
              </el-input>
              <p class="port-desc">MaiBot主程序监听端口</p>
            </div>

            <div class="port-item">
              <el-input
                v-model="adapterPort"
                type="number"
                placeholder="适配器端口">
                <template #prepend>适配器端口</template>
              </el-input>
              <p class="port-desc">NapCat适配器监听端口</p>
            </div>
            
            <div class="port-item">
              <el-input
                v-model="napcatPort"
                type="number"
                placeholder="NapCat端口">
                <template #prepend>NapCat端口</template>
              </el-input>
              <p class="port-desc">NapCat的WebSocket服务器端口</p>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, onUnmounted, inject } from 'vue';
import { ElMessage } from 'element-plus';
import { Download, User } from '@element-plus/icons-vue';
import axios from 'axios';
import * as deployApi from '../../api/deploy'; // 导入新的API服务

// ===================================
// 这些是Vue编译器宏，不需要导入
// 编辑器可能会报错，但Vue会正确处理它们
// ===================================

/**
 * 组件属性
 */
const props = defineProps({
  logCallback: Function
});

/**
 * 组件事件
 */
const emit = defineEmits(['refresh-instances', 'add-log']);

// 实例安装状态变量
const selectedVersion = ref('');
const availableVersions = ref([]);
const versionsLoading = ref(false);
const installLoading = ref(false);
const versionError = ref('');
const installStatus = ref('idle');  // idle, installing, completed, failed

// 添加表单对象用于输入验证
const form = ref({});

// 添加实例名称
const instanceName = ref('');

// Bot配置选项
const installNapcat = ref(true);
const installAdapter = ref(true);
const qqNumber = ref('');

// 端口配置 - 添加适配器端口
const napcatPort = ref('8095');     // NapCat默认端口
const adapterPort = ref('18002');   // 适配器默认端口
const maibotPort = ref('8000');     // MaiBot默认端口

// 是否可以安装Bot
const canConfigureBot = computed(() => {
  // 首先检查实例名称
  if (!instanceName.value || instanceName.value.trim() === '') {
    return false;
  }
  
  // 如果启用了适配器或NapCat，检查QQ号
  if (installNapcat.value || installAdapter.value) {
    return qqNumber.value.trim() !== '' && /^\d+$/.test(qqNumber.value);
  }
  
  return true;
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
        // 使用新的API服务获取版本
        const versions = await deployApi.fetchVersions();

        if (versions && versions.length > 0 && 
            !(versions.length === 1 && versions[0] === 'NaN')) {
          availableVersions.value = versions;
          success = true;
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
  
  // 检查实例名称
  if (!instanceName.value || instanceName.value.trim() === '') {
    ElMessage.error('请输入实例名称');
    return;
  }
  
  // 检查Bot配置
  if ((installNapcat.value || installAdapter.value) && !canConfigureBot.value) {
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
      message: `$ 开始安装 ${selectedVersion.value}，实例名称：${instanceName.value}...`
    });
    
    // 1. 首先使用API安装MaiBot实例，传递实例名称
    // 修改：显式使用更可靠的端点
    const deployResult = await deployApi.deployVersion(selectedVersion.value, instanceName.value);
    
    if (!deployResult.success) {
      ElMessage.error(deployResult.message || '安装失败');
      installStatus.value = 'failed';
      addLog({
        time: formatTime(new Date()),
        source: 'command',
        level: 'ERROR',
        message: `$ 无法安装 ${selectedVersion.value}: ${deployResult.message || '未知错误'}`
      });
      installLoading.value = false;
      return;
    }
    
    addLog({
      time: formatTime(new Date()),
      source: 'command',
      level: 'SUCCESS',
      message: `$ ${instanceName.value} (${selectedVersion.value}) 基础安装完成`
    });
    
    // 2. 然后配置NapCat和适配器 (如果启用)
    if (installNapcat.value || installAdapter.value) {
      // 添加命令行指示符
      addLog({
        time: formatTime(new Date()),
        source: 'command',
        level: 'INFO',
        message: `$ 正在开始配置Bot环境...`
      });
      
      // 如果启用了各组件，显示对应的安装指示
      if (installAdapter.value) {
        addLog({
          time: formatTime(new Date()),
          source: 'command',
          level: 'INFO', 
          message: `$ 安装 NapCat 适配器...`
        });
      }
      
      if (installNapcat.value) {
        addLog({
          time: formatTime(new Date()),
          source: 'command',
          level: 'INFO',
          message: `$ 配置 NapCat (QQ: ${qqNumber.value || '未指定'}, 端口: ${napcatPort.value})...`
        });
      }
      
      // 开始进行配置并安装 - 使用新API，传递实例名称和适配器端口
      const configResponse = await deployApi.configureBot({
        instance_name: instanceName.value,
        qq_number: qqNumber.value,
        install_napcat: installNapcat.value,
        install_nonebot: false, // 已移除，设为false
        run_install_script: true, // 保持为true，后端需要
        install_adapter: installAdapter.value,
        ports: {
          napcat: parseInt(napcatPort.value),
          adapter: parseInt(adapterPort.value),
          maibot: parseInt(maibotPort.value)
        }
      });
      
      if (configResponse.success) {
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
          message: `$ Bot配置部分失败: ${configResponse.message || '未知原因'}`
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
    { name: 'MaiBot', value: maibotPort.value },
    { name: 'NapCat适配器', value: adapterPort.value },
    { name: 'NapCat', value: napcatPort.value }
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
    // 使用新API检查安装状态
    return await deployApi.checkInstallStatus();
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
watch(selectedVersion, (newVal) => {
  if (newVal) {
    // 如果选择了版本，提供默认实例名称
    if (!instanceName.value) {
      instanceName.value = `MaiBot-${newVal}`;
    }
    
    installAdapter.value = true;
    installNapcat.value = true;
    qqNumber.value = '';
    napcatPort.value = '8095';
    adapterPort.value = '18002';
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

<style>
@import '../../assets/css/downloads/installConfig.css';

/* 添加动画效果 */
.config-fade-enter-active,
.config-fade-leave-active {
  transition: all 0.5s ease;
  max-height: 2000px;
  opacity: 1;
  overflow: hidden;
}

.config-fade-enter-from,
.config-fade-leave-to {
  max-height: 0;
  opacity: 0;
  overflow: hidden;
  margin-top: 0;
  margin-bottom: 0;
  padding-top: 0;
  padding-bottom: 0;
}

/* 实例名称输入样式 */
.instance-name-input {
  margin-bottom: 20px;
}

/* 修复边距问题 */
.el-form-item {
  margin-bottom: 15px;
}

.el-form-item__label {
  padding-bottom: 6px;
  font-weight: 500;
}

/* 确保表单布局正确 */
.el-form {
  width: 100%;
}

/* 修复端口配置布局 */
.ports-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}

@media (max-width: 768px) {
  .ports-grid {
    grid-template-columns: 1fr;
  }
}
</style>

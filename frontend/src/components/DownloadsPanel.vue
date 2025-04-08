<template>
  <div class="downloads-tab">
    <div class="header-section">
      <h3>下载管理</h3>
      <el-button type="primary" @click="refreshDownloads" size="small">刷新</el-button>
    </div>

    <!-- 添加版本安装部分 -->
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
        
        <!-- 配置日志 -->
        <div class="config-logs" v-if="configLogs.length > 0">
          <el-divider content-position="left">安装日志</el-divider>
          <div class="logs-container">
            <div v-for="(log, index) in configLogs" :key="index" class="log-item">
              <div class="log-source" :class="log.source">{{ getSourceLabel(log.source) }}</div>
              <div class="log-content" :class="log.level.toLowerCase()">{{ log.message }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 下载任务列表 -->
    <div class="section">
      <div class="section-title">下载任务</div>
      <div class="downloads-container">
        <el-table 
          :data="downloads" 
          style="width: 100%" 
          v-loading="loading"
          :empty-text="loading ? '加载中...' : '暂无下载任务'">
          <el-table-column prop="name" label="文件名" min-width="180" />
          <el-table-column prop="progress" label="进度" width="180">
            <template #default="{row}">
              <el-progress :percentage="row.progress" :status="row.status === '失败' ? 'exception' : null" />
            </template>
          </el-table-column>
          <el-table-column prop="speed" label="速度" width="120" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{row}">
              <el-tag :type="getStatusType(row.status)">
                {{ row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{row}">
              <el-button 
                v-if="row.status === '等待' || row.status === '暂停'" 
                type="primary" 
                size="small" 
                circle
                @click="startDownload(row.id)">
                <el-icon><VideoPlay /></el-icon>
              </el-button>
              <el-button 
                v-if="row.status === '下载中'"
                type="warning" 
                size="small" 
                circle
                @click="pauseDownload(row.id)">
                <el-icon><VideoPause /></el-icon>
              </el-button>
              <el-button 
                v-if="row.status === '完成'"
                type="success" 
                size="small" 
                circle
                @click="openFile(row.path)">
                <el-icon><FolderOpened /></el-icon>
              </el-button>
              <el-button 
                type="danger" 
                size="small" 
                circle
                @click="confirmDeleteDownload(row.id)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <div class="add-download-section">
      <el-button type="primary" @click="showAddDownloadDialog">
        <el-icon><Plus /></el-icon> 添加下载
      </el-button>
    </div>

    <!-- 添加下载对话框 -->
    <el-dialog v-model="addDownloadDialogVisible" title="添加下载任务" width="500px">
      <el-form :model="newDownload" label-width="80px">
        <el-form-item label="类型">
          <el-radio-group v-model="newDownload.type">
            <el-radio-button label="repository">Git仓库</el-radio-button>
            <el-radio-button label="file">文件</el-radio-button>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="地址">
          <el-input 
            v-model="newDownload.url" 
            placeholder="请输入下载地址"
            :prefix-icon="newDownload.type === 'repository' ? 'el-icon-link' : 'el-icon-document'" />
        </el-form-item>
        
        <el-form-item v-if="newDownload.type === 'repository'" label="分支">
          <el-input v-model="newDownload.branch" placeholder="master" />
        </el-form-item>
        
        <el-form-item label="保存到">
          <el-input 
            v-model="newDownload.path" 
            placeholder="选择保存路径">
            <template #append>
              <el-button @click="selectFolder">浏览</el-button>
            </template>
          </el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="addDownloadDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="addDownload" :disabled="!isValidDownload">
            添加
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch, inject } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Download, Delete, VideoPlay, VideoPause, FolderOpened, Plus, User } from '@element-plus/icons-vue';
import axios from 'axios';

// 事件总线，用于与其他组件通信
const emitter = inject('emitter');

// 下载管理状态变量
const downloads = ref([
  { id: 1, name: 'MaiBot-v2.1.0.zip', progress: 100, speed: '0 KB/s', status: '完成', path: 'D:/Downloads/MaiBot-v2.1.0.zip' },
  { id: 2, name: 'Resources-pack.rpk', progress: 65, speed: '1.2 MB/s', status: '下载中', path: 'D:/Downloads/Resources-pack.rpk' },
  { id: 3, name: 'Update-patch.exe', progress: 0, speed: '0 KB/s', status: '等待', path: 'D:/Downloads/Update-patch.exe' },
]);
const loading = ref(false);
const addDownloadDialogVisible = ref(false);
const newDownload = ref({
  type: 'repository',
  url: '',
  branch: 'master',
  path: ''
});

// 实例安装状态变量
const selectedVersion = ref('');
const availableVersions = ref([]);
const versionsLoading = ref(false);
const installLoading = ref(false);
const versionError = ref('');

// Bot配置选项
const installNapcat = ref(true);
const installNonebot = ref(true);
const runInstallScript = ref(false);  // 新增运行安装脚本选项
const qqNumber = ref('');
const configLogs = ref([]);

let pollingInterval = null;
let wsConnection = null;

// 计算属性
const isValidDownload = computed(() => {
  return newDownload.value.url.trim() !== '' && newDownload.value.path.trim() !== '';
});

// 是否可以安装Bot
const canConfigureBot = computed(() => {
  if (!installNapcat.value && !installNonebot.value) return true;
  return qqNumber.value.trim() !== '' && /^\d+$/.test(qqNumber.value);
});

// 下载管理方法
const refreshDownloads = async () => {
  loading.value = true;
  try {
    const response = await axios.get('/api/downloads');
    if (response.data && response.data.downloads) {
      downloads.value = response.data.downloads;
    } else {
      downloads.value = [];
    }
  } catch (error) {
    console.error('获取下载列表失败:', error);
    // 更详细的错误处理
    if (error.response) {
      // 服务器返回了错误状态码
      ElMessage.error(`服务器错误: ${error.response.status} - ${error.response.data?.detail || '未知错误'}`);
    } else if (error.request) {
      // 请求已发送但没有收到响应
      ElMessage.error('无法连接到后端服务，请确认后端服务已启动');
    } else {
      // 其他错误
      ElMessage.error(`请求设置错误: ${error.message}`);
    }
  } finally {
    loading.value = false;
  }
};

const startDownload = async (id) => {
  try {
    await axios.post(`/api/downloads/${id}/start`);
    ElMessage.success('下载已开始');
    refreshDownloads();
  } catch (error) {
    ElMessage.error('启动下载失败');
  }
};

const pauseDownload = async (id) => {
  try {
    await axios.post(`/api/downloads/${id}/pause`);
    ElMessage.success('下载已暂停');
    refreshDownloads();
  } catch (error) {
    ElMessage.error('暂停下载失败');
  }
};

const openFile = (path) => {
  axios.post('/api/open-path', { path })
    .catch(error => {
      ElMessage.error('无法打开文件');
    });
};

const confirmDeleteDownload = (id) => {
  ElMessageBox.confirm(
    '确定要删除此下载任务吗？',
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    deleteDownload(id);
  }).catch(() => {});
};

const deleteDownload = async (id) => {
  try {
    await axios.delete(`/api/downloads/${id}`);
    ElMessage.success('下载已删除');
    refreshDownloads();
  } catch (error) {
    ElMessage.error('删除下载失败');
  }
};

const showAddDownloadDialog = () => {
  newDownload.value = {
    type: 'repository',
    url: '',
    branch: 'master',
    path: ''
  };
  addDownloadDialogVisible.value = true;
};

const selectFolder = async () => {
  try {
    const response = await axios.get('/api/select-folder');
    if (response.data && response.data.path) {
      newDownload.value.path = response.data.path;
    }
  } catch (error) {
    ElMessage.error('选择文件夹失败');
  }
};

const addDownload = async () => {
  if (!isValidDownload.value) return;
  
  try {
    const response = await axios.post('/api/downloads', newDownload.value);
    if (response.data && response.data.success) {
      ElMessage.success('下载任务已添加');
      addDownloadDialogVisible.value = false;
      refreshDownloads();
    } else {
      ElMessage.error(response.data.message || '添加下载失败');
    }
  } catch (error) {
    ElMessage.error('添加下载失败');
  }
};

// 版本安装方法
const fetchVersions = async () => {
  versionsLoading.value = true;
  versionError.value = '';
  try {
    const response = await axios.get('/api/versions');
    if (response.data && response.data.versions) {
      if (response.data.versions.length === 0 || 
          (response.data.versions.length === 1 && response.data.versions[0] === 'NaN')) {
        versionError.value = '无法获取版本列表，可能是仓库访问问题，请检查网络连接';
        availableVersions.value = [];
      } else {
        availableVersions.value = response.data.versions;
      }
    } else {
      availableVersions.value = [];
      ElMessage.warning('未获取到可用版本');
    }
  } catch (error) {
    console.error('获取版本列表失败:', error);
    versionError.value = '获取版本列表失败: ' + (error.response?.data?.detail || error.message);
    ElMessage.error('获取版本列表失败');
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
  
  installLoading.value = true;
  configLogs.value = []; // 清空配置日志
  
  try {
    // 1. 首先安装MaiBot实例
    const response = await axios.post(`/api/deploy/${selectedVersion.value}`);
    
    if (!response.data.success) {
      ElMessage.error(response.data.message || '安装失败');
      return;
    }
    
    ElMessage.success(`${selectedVersion.value} 安装成功`);
    
    // 2. 然后配置NapCat和NoneBot (如果启用)
    if (installNapcat.value || installNonebot.value || runInstallScript.value) {
      // 开始进行配置并安装
      const configResponse = await axios.post('/api/install/configure', {
        qq_number: qqNumber.value,
        install_napcat: installNapcat.value,
        install_nonebot: installNonebot.value,
        run_install_script: runInstallScript.value  // 添加安装脚本选项
      });
      
      if (configResponse.data.success) {
        ElMessage.success('Bot配置完成');
      } else {
        ElMessage.warning(`Bot配置部分失败: ${configResponse.data.message}`);
      }
    }
    
    // 通知更新实例列表
    if (emitter) {
      emitter.emit('refresh-instances');
    }
    
    ElMessage({
      message: '实例已安装，请在实例管理中查看',
      type: 'success',
      duration: 5000
    });
  } catch (error) {
    console.error('版本安装失败:', error);
    ElMessage.error('安装失败: ' + (error.response?.data?.detail || error.message));
  } finally {
    installLoading.value = false;
  }
};

// WebSocket连接
const setupWebSocket = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.host;
  const wsUrl = `${protocol}//${host}/api/logs/ws`;
  
  wsConnection = new WebSocket(wsUrl);
  
  wsConnection.onmessage = (event) => {
    try {
      const logData = JSON.parse(event.data);
      
      // 处理安装日志
      if (logData.source === 'napcat' || logData.source === 'nonebot' || logData.source === 'install') {
        configLogs.value.push(logData);
        
        // 限制日志条数
        if (configLogs.value.length > 100) {
          configLogs.value = configLogs.value.slice(-100);
        }
        
        // 自动滚动到底部
        setTimeout(() => {
          const container = document.querySelector('.logs-container');
          if (container) {
            container.scrollTop = container.scrollHeight;
          }
        }, 50);
      }
    } catch (error) {
      console.error('处理WebSocket消息失败:', error);
    }
  };
  
  wsConnection.onerror = (error) => {
    console.error('WebSocket错误:', error);
  };
  
  wsConnection.onclose = () => {
    console.log('WebSocket连接已关闭，尝试重连...');
    setTimeout(setupWebSocket, 3000);
  };
};

// 获取日志源标签
const getSourceLabel = (source) => {
  switch(source) {
    case 'napcat': return 'NapCat';
    case 'nonebot': return 'NoneBot';
    case 'install': return '安装';
    default: return source;
  }
};

// 辅助函数
const getStatusType = (status) => {
  switch (status) {
    case '完成': return 'success';
    case '下载中': return 'primary';
    case '等待': return 'info';
    case '暂停': return 'warning';
    case '失败': return 'danger';
    default: return 'info';
  }
};

// 定期刷新下载状态
const startPolling = () => {
  pollingInterval = setInterval(refreshDownloads, 3000);
};

const stopPolling = () => {
  if (pollingInterval) {
    clearInterval(pollingInterval);
  }
};

// 生命周期钩子
onMounted(() => {
  // 启动时添加延迟，确保后端服务已启动
  setTimeout(() => {
    refreshDownloads();
    fetchVersions();
    setupWebSocket();
    startPolling();
  }, 1000);
});

onBeforeUnmount(() => {
  stopPolling();
  if (wsConnection) {
    wsConnection.close();
  }
});

// 监听版本变化，重置配置
watch(selectedVersion, () => {
  if (selectedVersion.value) {
    installNapcat.value = true;
    installNonebot.value = true;
    qqNumber.value = '';
    configLogs.value = [];
  }
});
</script>

<style scoped>
.downloads-tab {
  width: 100%;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section {
  margin-bottom: 24px;
  background-color: #f9f9f9;
  border-radius: 8px;
  padding: 16px;
}

.section-title {
  font-weight: bold;
  font-size: 16px;
  margin-bottom: 12px;
  color: var(--el-color-primary);
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 8px;
}

.install-container {
  display: flex;
  gap: 12px;
  align-items: center;
}

.downloads-container {
  margin-bottom: 10px;
}

.add-download-section {
  display: flex;
  justify-content: center;
  margin-top: 20px;
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

/* 配置日志样式 */
.logs-container {
  height: 200px;
  overflow-y: auto;
  background: #1e1e1e;
  border-radius: 4px;
  padding: 8px;
  font-family: Consolas, Monaco, 'Andale Mono', monospace;
  font-size: 13px;
}

.log-item {
  display: flex;
  margin-bottom: 4px;
  color: #d4d4d4;
}

.log-source {
  min-width: 80px;
  padding: 2px 6px;
  margin-right: 8px;
  border-radius: 3px;
  text-align: center;
  font-weight: bold;
  font-size: 12px;
}

.log-source.napcat {
  background-color: #42b983;
  color: white;
}

.log-source.nonebot {
  background-color: #6495ed;
  color: white;
}

.log-source.install {
  background-color: #9370db;
  color: white;
}

.log-content {
  flex: 1;
  white-space: pre-wrap;
  word-break: break-all;
}

.log-content.error {
  color: #ff6b6b;
}

.log-content.warning {
  color: #ffb347;
}

.log-content.success {
  color: #42b983;
}

/* 下载表格动画 */
.el-table :deep(.el-table__row) {
  transition: background-color 0.3s ease;
}
.el-table :deep(.el-table__row:hover) {
  background-color: var(--el-color-primary-light-9);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .install-container, .config-options {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>

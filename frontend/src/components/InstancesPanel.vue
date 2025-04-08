<template>
  <div class="instances-tab">
    <div class="header-section">
      <h3>Bot 实例管理</h3>
      <el-button type="primary" @click="fetchInstalledVersions" size="small">刷新</el-button>
    </div>

    <!-- 已安装实例管理 -->
    <div class="section">
      <div class="section-title">已安装实例</div>
      <el-empty v-if="installedVersions.length === 0" description="暂无已安装实例" />
      <div v-else class="instance-grid">
        <el-card 
          v-for="instance in installedVersions" 
          :key="instance.name"
          class="instance-card"
          :class="{'running': instance.status === 'running'}">
          <template #header>
            <div class="instance-header">
              <span class="instance-name">{{ instance.name }}</span>
              <el-tag :type="getStatusType(instance.status)" size="small">{{ getStatusText(instance.status) }}</el-tag>
            </div>
          </template>
          
          <div class="instance-info">
            <p><strong>路径:</strong> {{ instance.path }}</p>
            <p><strong>安装时间:</strong> {{ instance.installedAt }}</p>
          </div>
          
          <div class="instance-actions">
            <el-button 
              v-if="instance.status !== 'running'" 
              type="success" 
              size="small" 
              @click="startBot(instance.name)">
              启动
            </el-button>
            <el-button 
              v-else
              type="danger" 
              size="small" 
              @click="stopBot(instance.name)">
              停止
            </el-button>
            <el-dropdown trigger="click">
              <el-button type="info" size="small">
                更多 <el-icon><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="showLogs(instance.name)">查看日志</el-dropdown-item>
                  <el-dropdown-item @click="updateInstance(instance.name)">更新</el-dropdown-item>
                  <el-dropdown-item @click="openFolder(instance.path)">打开文件夹</el-dropdown-item>
                  <el-dropdown-item divided @click="confirmDelete(instance.name)">
                    <span style="color: #f56c6c">删除</span>
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-card>
      </div>
    </div>

    <div class="tip-section">
      <el-alert
        type="info"
        show-icon
        :closable="false">
        <template #title>
          <span>需要添加新的Bot实例？请前往<el-link @click="goToDownloads" type="primary">下载管理</el-link>页面</span>
        </template>
      </el-alert>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, inject, onUnmounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { ArrowDown } from '@element-plus/icons-vue';
import axios from 'axios';

// 事件总线，用于与LogsPanel通信
const emitter = inject('emitter');

// 状态变量
const installedVersions = ref([]);

// 事件处理
const fetchInstalledVersions = async () => {
  try {
    const response = await axios.get('/api/instances');
    installedVersions.value = response.data.instances || [];
  } catch (error) {
    console.error('获取已安装实例失败:', error);
    ElMessage.error('获取已安装实例失败');
  }
};

const startBot = async (instanceName) => {
  try {
    const response = await axios.post(`/api/start/${instanceName}`);
    if (response.data.success) {
      ElMessage.success('机器人已启动');
      fetchInstalledVersions();
    } else {
      ElMessage.error('启动失败');
    }
  } catch (error) {
    console.error('启动失败:', error);
    ElMessage.error('启动失败: ' + (error.response?.data?.detail || error.message));
  }
};

const stopBot = async (instanceName) => {
  try {
    const response = await axios.post('/api/stop');
    if (response.data.success) {
      ElMessage.success('机器人已停止');
      fetchInstalledVersions();
    } else {
      ElMessage.error('停止失败');
    }
  } catch (error) {
    console.error('停止失败:', error);
    ElMessage.error('停止失败: ' + (error.response?.data?.detail || error.message));
  }
};

const updateInstance = async (instanceName) => {
  try {
    const response = await axios.post(`/api/update/${instanceName}`);
    if (response.data.success) {
      ElMessage.success('更新成功');
      fetchInstalledVersions();
    } else {
      ElMessage.error('更新失败');
    }
  } catch (error) {
    console.error('更新失败:', error);
    ElMessage.error('更新失败');
  }
};

const showLogs = (instanceName) => {
  // 通过事件总线切换到日志面板并选择对应实例的日志
  if (emitter) {
    emitter.emit('show-instance-logs', instanceName);
  }
};

const openFolder = (path) => {
  // 通过后端API打开文件夹
  axios.post('/api/open-folder', { path })
    .catch(error => {
      console.error('无法打开文件夹:', error);
      ElMessage.error('无法打开文件夹');
    });
};

const confirmDelete = (instanceName) => {
  ElMessageBox.confirm(
    `确定要删除实例 ${instanceName} 吗？`,
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(() => {
    deleteInstance(instanceName);
  }).catch(() => {});
};

const deleteInstance = async (instanceName) => {
  try {
    const response = await axios.delete(`/api/instance/${instanceName}`);
    if (response.data.success) {
      ElMessage.success('删除成功');
      fetchInstalledVersions();
    } else {
      ElMessage.error('删除失败');
    }
  } catch (error) {
    console.error('删除失败:', error);
    ElMessage.error('删除失败');
  }
};

// 辅助函数
const getStatusType = (status) => {
  switch (status) {
    case 'running': return 'success';
    case 'stopped': return 'info';
    default: return 'info';
  }
};

const getStatusText = (status) => {
  switch (status) {
    case 'running': return '运行中';
    case 'stopped': return '已停止';
    default: return '未知';
  }
};

// 导航到下载页面
const goToDownloads = () => {
  if (emitter) {
    emitter.emit('navigate-to-tab', 'downloads');
  }
};

// 初始化
onMounted(() => {
  fetchInstalledVersions();
  
  // 监听刷新实例列表事件
  if (emitter) {
    emitter.on('refresh-instances', fetchInstalledVersions);
  }
});

// 移除事件监听器
onUnmounted(() => {
  if (emitter) {
    emitter.off('refresh-instances', fetchInstalledVersions);
  }
});
</script>

<style scoped>
.instances-tab {
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

.instance-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  margin-top: 8px;
}

.instance-card {
  transition: all 0.3s ease;
}

.instance-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
}

.instance-card.running {
  border-left: 4px solid var(--el-color-success);
}

.instance-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.instance-name {
  font-weight: bold;
}

.instance-info {
  font-size: 14px;
  margin: 8px 0;
  color: #666;
}

.instance-info p {
  margin: 5px 0;
}

.instance-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 12px;
}

.tip-section {
  margin-top: 16px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .instance-grid {
    grid-template-columns: 1fr;
  }
}
</style>

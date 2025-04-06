<template>
  <div class="container">
    <el-card class="deploy-card">
      <template #header>
        <div class="card-header">
          <h2>MaiBot 部署站</h2>
        </div>
      </template>
      
      <el-form>
        <el-form-item label="选择版本">
          <el-select v-model="selectedVersion" placeholder="请选择版本">
            <el-option
              v-for="version in versions"
              :key="version"
              :label="version"
              :value="version"
            />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleDeploy" :loading="deploying">
            部署
          </el-button>
          <el-button type="success" @click="handleStart" :loading="starting">
            启动机器人
          </el-button>
        </el-form-item>
      </el-form>

      <div class="status-area">
        <el-alert
          v-if="message"
          :title="message"
          :type="messageType"
          show-icon
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const versions = ref([])
const selectedVersion = ref('')
const deploying = ref(false)
const starting = ref(false)
const message = ref('')
const messageType = ref('info')

onMounted(async () => {
  try {
    const response = await axios.get('/api/versions')
    versions.value = response.data.versions
  } catch (error) {
    showMessage('获取版本列表失败', 'error')
  }
})

const showMessage = (msg, type = 'success') => {
  message.value = msg
  messageType.value = type
}

const handleDeploy = async () => {
  if (!selectedVersion.value) {
    showMessage('请选择版本', 'warning')
    return
  }
  deploying.value = true
  try {
    const response = await axios.post(`/api/deploy/${selectedVersion.value}`)
    showMessage(response.data.message, response.data.status)
  } catch (error) {
    showMessage('部署失败', 'error')
  } finally {
    deploying.value = false
  }
}

const handleStart = async () => {
  if (!selectedVersion.value) {
    showMessage('请选择版本', 'warning')
    return
  }
  starting.value = true
  try {
    const response = await axios.post(`/api/start/${selectedVersion.value}`)
    showMessage(response.data.message, response.data.status)
  } catch (error) {
    showMessage('启动失败', 'error')
  } finally {
    starting.value = false
  }
}
</script>

<style scoped>
.container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: #f0f2f5;
}

.deploy-card {
  width: 480px;
}

.card-header {
  text-align: center;
}

.status-area {
  margin-top: 20px;
}
</style>

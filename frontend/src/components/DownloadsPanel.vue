<template>
  <div class="downloads-tab">
    <h3>下载管理</h3>
    <el-table :data="downloads" style="width: 100%">
      <el-table-column prop="name" label="文件名" width="180" />
      <el-table-column prop="progress" label="进度" width="180">
        <template #default="{row}">
          <el-progress :percentage="row.progress" />
        </template>
      </el-table-column>
      <el-table-column prop="speed" label="速度" />
      <el-table-column prop="status" label="状态">
        <template #default="{row}">
          <el-tag :type="row.status === '完成' ? 'success' : 'info'">
            {{ row.status }}
          </el-tag>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const downloads = ref([
  { name: 'MaiBot-v2.1.0.zip', progress: 100, speed: '0 KB/s', status: '完成' },
  { name: 'Resources-pack.rpk', progress: 65, speed: '1.2 MB/s', status: '下载中' },
  { name: 'Update-patch.exe', progress: 0, speed: '0 KB/s', status: '等待' }
])
</script>

<style scoped>
.downloads-tab {
  width: 100%;
}

/* 下载表格动画 */
.el-table :deep(.el-table__row) {
  transition: background-color 0.3s ease;
}
.el-table :deep(.el-table__row:hover) {
  background-color: var(--el-color-primary-light-9);
}
</style>

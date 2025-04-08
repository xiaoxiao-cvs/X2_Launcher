<template>
  <el-card shadow="hover" class="status-card">
    <template #header>
      <div class="card-header">
        <span>系统状态</span>
      </div>
    </template>
    <div class="card-content">
      <p>MongoDB: <el-tag type="success">（系统服务）运行中</el-tag></p>
      <p>NapCat 服务器: <el-tag type="warning">已停止</el-tag></p>
      <p>MaiM-Core: <el-tag type="danger">未运行</el-tag></p>
    </div>
  </el-card>
</template>

<style scoped>
.status-card {
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  border-radius: 8px;
}
.status-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
}

.card-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
</style>

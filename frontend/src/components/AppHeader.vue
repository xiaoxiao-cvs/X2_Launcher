<template>
  <div class="header">
    <div class="logo-area">
      <div class="logo-icon">
        <svg width="24" height="24" viewBox="0 0 24 24">
          <polygon points="12,2 22,22 2,22" fill="#409EFF"/>
        </svg>
      </div>
      <h1>𝕏² Launcher</h1>
    </div>
    
    <div class="action-buttons">
      <el-button type="success" size="small"></el-button>
      <el-button type="info" size="small">启动MaiBot主程序</el-button>
      <el-button type="primary" size="small">关闭</el-button>
    </div>
  </div>
</template>

<style scoped>
.header {
  padding: 0 20px;
  background-color: white;
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 60px;
}

.logo-area {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo-icon {
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-buttons {
  display: flex;
  gap: 8px;
}
</style>

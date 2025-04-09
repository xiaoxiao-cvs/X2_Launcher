<template>
  <div class="sidebar">
    <el-menu 
      :default-active="activeTab" 
      @select="handleSelect"
      class="sidebar-menu">
      <el-menu-item index="home" class="menu-item">
        <el-icon><House /></el-icon>
        <span>首页</span>
      </el-menu-item>
      <el-menu-item index="instances" class="menu-item">
        <el-icon><Menu /></el-icon>
        <span>实例</span>
      </el-menu-item>
      <el-menu-item index="downloads" class="menu-item">
        <el-icon><Download /></el-icon>
        <span>下载</span>
      </el-menu-item>
      <el-menu-item index="logs" class="menu-item">
        <el-icon><Notebook /></el-icon>
        <span>日志</span>
      </el-menu-item>
      <el-menu-item index="settings" class="menu-item">
        <el-icon><Setting /></el-icon>
        <span>设置</span>
      </el-menu-item>
    </el-menu>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue'
import { House, Menu, Setting, Download, Notebook } from '@element-plus/icons-vue'

const props = defineProps({
  activeTab: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['select'])

const handleSelect = (index) => {
  emit('select', index)
}
</script>

<style scoped>
.sidebar {
  width: 200px;
  background-color: var(--el-bg-color, white);
  border-right: 1px solid var(--el-border-color-lighter, #e6e6e6);
  height: 100%;
  overflow-y: auto;
  border-radius: 0 0 0 8px;
  transition: background-color 0.3s, border-color 0.3s;
}

/* 菜单项动画 */
.menu-item {
  transition: all 0.3s ease;
  border-radius: 6px;
  margin: 4px 8px;
  color: var(--el-text-color-primary);
}
.menu-item:hover {
  background-color: var(--el-color-primary-light-9);
  transform: translateX(3px);
}
.menu-item.is-active {
  background-color: var(--el-color-primary-light-8);
}

@media (max-width: 768px) {
  .sidebar {
    width: 100%;
    height: auto;
    border-right: none;
    border-bottom: 1px solid var(--el-border-color-lighter);
  }
}
</style>

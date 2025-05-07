<template>
  <div class="side-nav" :class="{ expanded: isExpanded }">
    <div class="side-nav-content">
      <!-- 导航栏 Logo -->
      <div class="nav-logo" @click="$emit('toggle')">
        <el-icon size="large"><HomeFilled /></el-icon>
        <span class="nav-text">X² Launcher</span>
      </div>

      <!-- 导航项 -->
      <div class="nav-items">
        <div 
          v-for="(item, key) in menuItems" 
          :key="key"
          class="nav-item"
          :class="{ active: activeTab === key }"
          @click="navigateTo(key)"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span class="nav-text">{{ item.title }}</span>
        </div>
      </div>
      
      <!-- 底部设置 -->
      <div class="nav-bottom" @click="$emit('toggle')">
        <el-icon>
          <component :is="isExpanded ? 'ArrowLeftBold' : 'ArrowRightBold'" />
        </el-icon>
        <span class="nav-text">{{ isExpanded ? '收起' : '展开' }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, inject, watch, onMounted } from 'vue';
import { HomeFilled, ArrowLeftBold, ArrowRightBold } from '@element-plus/icons-vue';

// 从App.vue注入数据
const activeTab = inject('activeTab');
const emitter = inject('emitter');
const menuItems = inject('menuItems', {});

// 接收展开状态属性
const props = defineProps({
  isExpanded: {
    type: Boolean,
    default: false
  }
});

// 定义emit
const emit = defineEmits(['toggle']);

// 导航方法
const navigateTo = (tabName) => {
  emitter.emit('navigate-to-tab', tabName);
};
</script>

<style>
@import '../assets/css/appSidebar.css';
</style>

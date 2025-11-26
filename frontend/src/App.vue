<template>
  <el-container class="layout-container">
    <el-aside width="240px" class="app-sidebar">
      <div class="logo-section">
        <el-icon class="logo-icon"><UserFilled /></el-icon>
        <h1 class="app-title">人脸门禁系统</h1>
      </div>
      
      <el-menu
        :default-active="activeIndex"
        class="sidebar-menu"
        :router="true"
        background-color="#001529"
        text-color="rgba(255, 255, 255, 0.65)"
        active-text-color="#fff"
      >
        <el-menu-item index="/">
          <el-icon><Monitor /></el-icon>
          <span>监控面板</span>
        </el-menu-item>
        <el-menu-item index="/admin">
          <el-icon><Setting /></el-icon>
          <span>系统管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    
    <el-container>
      <el-header class="app-header">
        <div class="header-left">
          <h2 class="page-title">{{ pageTitle }}</h2>
        </div>
        <div class="header-right">
          <div class="user-profile">
            <el-avatar :size="32" icon="UserFilled" />
            <span class="username">管理员</span>
          </div>
        </div>
      </el-header>
      
      <el-main class="app-main">
        <RouterView v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" :key="route.fullPath" />
          </transition>
        </RouterView>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { UserFilled, Monitor, Setting } from '@element-plus/icons-vue'

const route = useRoute()
const activeIndex = computed(() => route.path)

const pageTitle = computed(() => {
  switch (route.path) {
    case '/': return '监控面板'
    case '/admin': return '系统管理'
    default: return ''
  }
})
</script>

<style scoped>
.layout-container {
  height: 100vh;
  width: 100%;
}

.app-sidebar {
  background-color: #001529;
  color: white;
  display: flex;
  flex-direction: column;
  box-shadow: 2px 0 6px rgba(0, 21, 41, 0.35);
  z-index: 10;
}

.logo-section {
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 24px;
  background-color: #002140;
  gap: 12px;
}

.logo-icon {
  font-size: 24px;
  color: #1890ff;
}

.app-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: white;
  white-space: nowrap;
}

.sidebar-menu {
  border-right: none;
  flex: 1;
}

.app-header {
  background: #fff;
  height: 64px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  z-index: 9;
}

.page-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #262626;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background 0.3s;
}

.user-profile:hover {
  background: rgba(0, 0, 0, 0.025);
}

.username {
  font-size: 14px;
  color: #595959;
}

.app-main {
  background-color: #f0f2f5;
  padding: 24px;
  height: calc(100vh - 64px);
  overflow-y: auto;
}

/* 路由过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>

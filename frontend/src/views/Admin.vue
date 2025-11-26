<template>
  <div class="admin-panel">
    <div class="admin-header">
      <h1>系统管理</h1>
      <el-button type="primary" @click="openAddUser" v-if="activeTab === 'users'">
        <el-icon><Plus /></el-icon>
        添加用户
      </el-button>
    </div>
    
    <el-card class="admin-card" shadow="never">
      <el-tabs v-model="activeTab" class="admin-tabs">
        <el-tab-pane label="用户管理" name="users">
          <UserList ref="userListRef" @add-user="openAddUser" />
        </el-tab-pane>
        <el-tab-pane label="访问日志" name="logs">
          <LogTable />
        </el-tab-pane>
        <el-tab-pane label="系统设置" name="settings">
          <Settings />
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <AddUser ref="addUserRef" @success="onUserAdded" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import UserList from '../components/UserList.vue'
import AddUser from '../components/AddUser.vue'
import LogTable from '../components/LogTable.vue'
import Settings from '../components/Settings.vue'
import { Plus } from '@element-plus/icons-vue'

const activeTab = ref('users')
const userListRef = ref(null)
const addUserRef = ref(null)

const openAddUser = () => {
  addUserRef.value.open()
}

const onUserAdded = () => {
  if (userListRef.value) {
    userListRef.value.fetchUsers()
  }
}
</script>

<style scoped>
.admin-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.admin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.admin-header h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
}

.admin-card {
  flex: 1;
  display: flex;
  flex-direction: column;
}

:deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.admin-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
}

:deep(.el-tabs__content) {
  flex: 1;
  overflow-y: auto;
}
</style>

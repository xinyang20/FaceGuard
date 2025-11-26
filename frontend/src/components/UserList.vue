<template>
  <div class="user-list">
    <el-table :data="users" style="width: 100%" v-loading="loading" border stripe>
      <el-table-column prop="id" label="ID" width="80" align="center" />
      <el-table-column label="头像" width="100" align="center">
        <template #default="scope">
          <el-avatar :size="40" :src="scope.row.avatar_path" shape="square" />
        </template>
      </el-table-column>
      <el-table-column prop="name" label="姓名" min-width="120" />
      <el-table-column label="注册时间" min-width="180">
        <template #default="scope">
          {{ new Date().toLocaleString() }} <!-- 暂时使用当前时间，后续后端应返回注册时间 -->
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100" fixed="right" align="center">
        <template #default="scope">
          <el-button type="danger" link size="small" @click="handleDelete(scope.row)">
            <el-icon><Delete /></el-icon> 删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getUsers, deleteUser } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete } from '@element-plus/icons-vue'

const users = ref([])
const loading = ref(false)

const fetchUsers = async () => {
  loading.value = true
  try {
    users.value = await getUsers()
  } catch (e) {
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

const handleDelete = (user) => {
  ElMessageBox.confirm(
    `确定要删除用户 ${user.name} 吗？`,
    '警告',
    {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      await deleteUser(user.id)
      ElMessage.success('用户已删除')
      fetchUsers()
    } catch (e) {
      ElMessage.error('删除用户失败')
    }
  })
}

onMounted(fetchUsers)

defineExpose({ fetchUsers })
</script>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
</style>

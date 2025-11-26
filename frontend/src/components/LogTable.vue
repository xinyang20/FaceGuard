<template>
  <div class="log-table">
    <h2>访问日志</h2>
    <el-table :data="logs" style="width: 100%" v-loading="loading">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="timestamp" label="时间" width="180">
        <template #default="scope">
          {{ new Date(scope.row.timestamp).toLocaleString('zh-CN') }}
        </template>
      </el-table-column>
      <el-table-column label="快照" width="120">
        <template #default="scope">
          <el-image
            style="width: 100px; height: 100px"
            :src="scope.row.snapshot_path"
            :preview-src-list="[scope.row.snapshot_path]"
            fit="cover"
          />
        </template>
      </el-table-column>
      <el-table-column prop="user_name" label="姓名" />
      <el-table-column prop="status" label="状态">
        <template #default="scope">
          <el-tag :type="scope.row.status === 'PASS' ? 'success' : 'danger'">
            {{ scope.row.status === 'PASS' ? '通过' : '拒绝' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="confidence" label="置信度">
        <template #default="scope">
          {{ (scope.row.confidence * 100).toFixed(1) }}%
        </template>
      </el-table-column>
    </el-table>
    
    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        @current-change="fetchLogs"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getLogs } from '../api'
import { ElMessage } from 'element-plus'

const logs = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const fetchLogs = async () => {
  loading.value = true
  try {
    const res = await getLogs({ page: currentPage.value, size: pageSize.value })
    logs.value = res.items
    total.value = res.total
  } catch (e) {
    ElMessage.error('获取日志失败')
  } finally {
    loading.value = false
  }
}

onMounted(fetchLogs)
</script>

<style scoped>
.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>

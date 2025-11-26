<template>
  <div class="settings">
    <h2>系统设置</h2>
    <el-form :model="form" label-width="180px" style="max-width: 600px">
      <el-form-item label="帧间隔 (毫秒)">
        <el-input-number v-model="form.frame_interval_ms" :min="100" :max="5000" :step="100" />
      </el-form-item>
      <el-form-item label="识别阈值">
        <el-slider v-model="form.recognition_threshold" :min="0" :max="1" :step="0.01" show-input />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="saveConfig" :loading="loading">保存配置</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getConfig, updateConfig } from '../api'
import { ElMessage } from 'element-plus'

const form = ref({
  frame_interval_ms: 500,
  recognition_threshold: 0.6
})
const loading = ref(false)

const loadConfig = async () => {
  try {
    const res = await getConfig()
    if (res) form.value = res
  } catch (e) {
    ElMessage.error('加载配置失败')
  }
}

const saveConfig = async () => {
  loading.value = true
  try {
    await updateConfig(form.value)
    ElMessage.success('配置已保存')
  } catch (e) {
    ElMessage.error('保存配置失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadConfig)
</script>

<style scoped>
.settings {
  padding: 20px;
}
</style>

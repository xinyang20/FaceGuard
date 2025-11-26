<template>
  <el-dialog v-model="visible" title="注册新用户" width="500px">
    <el-form :model="form" label-width="80px">
      <el-form-item label="姓名">
        <el-input v-model="form.name" placeholder="请输入姓名" />
      </el-form-item>
      <el-form-item label="照片">
        <el-upload
          class="avatar-uploader"
          action="#"
          :auto-upload="false"
          :show-file-list="false"
          :on-change="handleFileChange"
        >
          <img v-if="imageUrl" :src="imageUrl" class="avatar" />
          <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
        </el-upload>
      </el-form-item>
    </el-form>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" @click="submit" :loading="loading">注册</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { addUser } from '../api'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

const emit = defineEmits(['success'])

const visible = ref(false)
const loading = ref(false)
const form = ref({ name: '' })
const file = ref(null)
const imageUrl = ref('')

const open = () => {
  form.value.name = ''
  file.value = null
  imageUrl.value = ''
  visible.value = true
}

const handleFileChange = (uploadFile) => {
  file.value = uploadFile.raw
  imageUrl.value = URL.createObjectURL(uploadFile.raw)
}

const submit = async () => {
  if (!form.value.name || !file.value) {
    ElMessage.warning('请提供姓名和照片')
    return
  }

  loading.value = true
  const formData = new FormData()
  formData.append('name', form.value.name)
  formData.append('photo', file.value)

  try {
    await addUser(formData)
    ElMessage.success('用户注册成功')
    visible.value = false
    emit('success')
  } catch (e) {
    // 显示后端返回的具体错误信息
    const errorMsg = e.response?.data?.detail || e.message || '用户注册失败'
    ElMessage.error(errorMsg)
    console.error('用户注册错误:', e.response?.data || e)
  } finally {
    loading.value = false
  }
}

defineExpose({ open })
</script>

<style scoped>
.avatar-uploader .el-upload {
  border: 1px dashed var(--el-border-color);
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: var(--el-transition-duration-fast);
}

.avatar-uploader .el-upload:hover {
  border-color: var(--el-color-primary);
}

.avatar-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 178px;
  height: 178px;
  text-align: center;
  line-height: 178px;
}

.avatar {
  width: 178px;
  height: 178px;
  display: block;
}
</style>

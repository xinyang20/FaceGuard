<template>
  <div class="image-recognition">
    <el-row :gutter="24">
      <el-col :lg="16" :md="24">
        <el-card class="upload-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <div class="header-left">
                <el-icon class="header-icon"><Picture /></el-icon>
                <span class="header-title">图片识别</span>
              </div>
              <div class="header-right">
                <el-button 
                  type="primary" 
                  size="small"
                  @click="switchToCamera"
                >
                  <el-icon><VideoCamera /></el-icon>
                  切换到摄像头
                </el-button>
              </div>
            </div>
          </template>
          
          <div class="upload-area">
            <!-- 上传按钮区域 -->
            <div class="upload-button-container">
              <el-button 
                type="default" 
                size="large"
                @click="triggerUpload"
                :loading="isProcessing"
                class="main-upload-btn"
              >
                <el-icon><UploadFilled /></el-icon>
                <span>选择图片进行识别</span>
              </el-button>
              <p class="upload-hint">支持 JPG、PNG 格式，文件大小不超过 10MB</p>
            </div>
            
            <!-- 隐藏的el-upload -->
            <el-upload
              ref="uploadRef"
              class="hidden-uploader"
              action="#"
              :auto-upload="false"
              :show-file-list="false"
              :on-change="handleFileChange"
              :accept="'image/jpeg,image/jpg,image/png'"
            >
            </el-upload>
          </div>
          
          <div v-if="imageUrl" class="preview-container">
            <div class="image-wrapper">
              <img ref="imageRef" :src="imageUrl" class="preview-image" @load="onImageLoad" />
              <canvas ref="canvasRef" class="overlay"></canvas>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :lg="8" :md="24">
        <div class="side-panel">
          <el-card class="result-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <el-icon class="header-icon"><DataAnalysis /></el-icon>
                <span class="header-title">识别结果</span>
              </div>
            </template>
            
            <div v-if="isProcessing" class="processing">
              <el-icon class="processing-icon"><Loading /></el-icon>
              <p>正在识别中...</p>
            </div>
            
            <div v-else-if="result" class="result-content">
              <div v-if="result.status === 'PASS'" class="result-pass">
                <div class="result-icon">
                  <el-icon><SuccessFilled /></el-icon>
                </div>
                <div class="result-info">
                  <h3 class="result-name">{{ result.name }}</h3>
                  <p class="result-status">验证通过</p>
                  <div class="confidence-bar">
                    <span class="confidence-label">置信度</span>
                    <el-progress 
                      :percentage="(result.confidence * 100).toFixed(1)"
                      :color="getConfidenceColor(result.confidence)"
                      :stroke-width="8"
                    />
                  </div>
                  <div class="result-details">
                    <el-tag type="success" size="small">已授权</el-tag>
                    <span class="timestamp">{{ new Date().toLocaleTimeString() }}</span>
                  </div>
                </div>
              </div>
              
              <div v-else-if="result.status === 'REJECT'" class="result-reject">
                <div class="result-icon">
                  <el-icon><CircleCloseFilled /></el-icon>
                </div>
                <div class="result-info">
                  <h3 class="result-name">未知人员</h3>
                  <p class="result-status">拒绝访问</p>
                  <el-tag type="danger" size="small">未授权</el-tag>
                  <div class="result-details">
                    <span class="timestamp">{{ new Date().toLocaleTimeString() }}</span>
                  </div>
                </div>
              </div>
              
              <div v-else class="result-no-face">
                <div class="result-icon">
                  <el-icon><UserFilled /></el-icon>
                </div>
                <div class="result-info">
                  <h3 class="result-name">未检测到人脸</h3>
                  <p class="result-status">请选择包含人脸的图片</p>
                  <el-tag type="warning" size="small">检测失败</el-tag>
                </div>
              </div>
            </div>
            
            <div v-else class="no-result">
              <el-icon class="no-result-icon"><Picture /></el-icon>
              <p>请上传图片进行识别</p>
            </div>
          </el-card>
          
          <el-card class="tips-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <el-icon class="header-icon"><InfoFilled /></el-icon>
                <span class="header-title">使用提示</span>
              </div>
            </template>
            
            <div class="tips-content">
              <div class="tip-item">
                <el-icon><Check /></el-icon>
                <span>确保图片中人脸清晰可见</span>
              </div>
              <div class="tip-item">
                <el-icon><Check /></el-icon>
                <span>建议使用正面人脸照片</span>
              </div>
              <div class="tip-item">
                <el-icon><Check /></el-icon>
                <span>避免光线过暗或过亮的环境</span>
              </div>
              <div class="tip-item">
                <el-icon><Check /></el-icon>
                <span>图片中最好只包含一个人脸</span>
              </div>
            </div>
          </el-card>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, watch, onUnmounted } from 'vue'
import { 
  UploadFilled, 
  Picture, 
  VideoCamera,
  DataAnalysis,
  SuccessFilled,
  CircleCloseFilled,
  UserFilled,
  InfoFilled,
  Check,
  Loading,
  Refresh
} from '@element-plus/icons-vue'
import { recognizeFace } from '../api'
import { ElMessage } from 'element-plus'

// 定义 emit
const emit = defineEmits(['mode-change'])

const uploadRef = ref(null)
const imageUrl = ref('')
const imageRef = ref(null)
const canvasRef = ref(null)
const result = ref(null)
const isProcessing = ref(false)

const triggerUpload = () => {
  if (uploadRef.value) {
    uploadRef.value.$el.querySelector('input[type=file]').click()
  }
}

const handleFileChange = async (file) => {
  // 验证文件类型
  const validTypes = ['image/jpeg', 'image/jpg', 'image/png']
  if (!validTypes.includes(file.raw.type)) {
    ElMessage.error('只支持 JPG 和 PNG 格式的图片')
    return
  }
  
  // 验证文件大小 (10MB)
  if (file.raw.size > 10 * 1024 * 1024) {
    ElMessage.error('图片大小不能超过 10MB')
    return
  }
  
  imageUrl.value = URL.createObjectURL(file.raw)
  result.value = null
  isProcessing.value = true
  
  // Clear canvas
  if (canvasRef.value) {
    const ctx = canvasRef.value.getContext('2d')
    ctx.clearRect(0, 0, canvasRef.value.width, canvasRef.value.height)
  }

  // Perform recognition
  const formData = new FormData()
  formData.append('file', file.raw)
  
  try {
    const res = await recognizeFace(formData)
    result.value = res
    
    if (res.status === 'PASS') {
      ElMessage.success(`识别成功：${res.name}`)
    } else if (res.status === 'REJECT') {
      ElMessage.warning('识别失败：未知人员')
    } else {
      ElMessage.info('未检测到人脸')
    }
  } catch (e) {
    ElMessage.error('识别失败，请重试')
    console.error(e)
  } finally {
    isProcessing.value = false
  }
}

const onImageLoad = () => {
  if (!result.value || !result.value.box || !imageRef.value || !canvasRef.value) return
  drawBox(result.value)
}

const switchToCamera = () => {
  // 清理当前状态
  if (imageUrl.value) {
    URL.revokeObjectURL(imageUrl.value)
    imageUrl.value = ''
  }
  result.value = null
  isProcessing.value = false
  
  emit('mode-change', 'camera')
}

// Watch for result change to draw if image is already loaded
watch(result, (newVal) => {
  if (newVal && imageRef.value && imageRef.value.complete) {
    drawBox(newVal)
  }
})

const drawBox = (res) => {
  const img = imageRef.value
  const canvas = canvasRef.value
  
  if (!img || !canvas || !res.box) return
  
  // Set canvas size to match image display size
  const rect = img.getBoundingClientRect()
  canvas.width = rect.width
  canvas.height = rect.height
  
  // Calculate scale factors
  const scaleX = img.naturalWidth / rect.width
  const scaleY = img.naturalHeight / rect.height
  
  const [x, y, w, h] = res.box
  const scaledX = x / scaleX
  const scaledY = y / scaleY
  const scaledW = w / scaleX
  const scaledH = h / scaleY
  
  const ctx = canvas.getContext('2d')
  
  // Clear previous drawings
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  
  // Draw bounding box
  ctx.lineWidth = 3
  ctx.strokeStyle = res.status === 'PASS' ? '#67C23A' : '#F56C6C'
  ctx.strokeRect(scaledX, scaledY, scaledW, scaledH)
  
  // Draw label background
  ctx.font = 'bold 14px Arial'
  const text = res.name || '未知'
  const textWidth = ctx.measureText(text).width
  
  ctx.fillStyle = res.status === 'PASS' ? '#67C23A' : '#F56C6C'
  ctx.fillRect(scaledX, scaledY - 22, textWidth + 8, 22)
  
  // Draw label text
  ctx.fillStyle = 'white'
  ctx.fillText(text, scaledX + 4, scaledY - 8)
}

const getConfidenceColor = (confidence) => {
  if (confidence >= 0.8) return '#67C23A'
  if (confidence >= 0.6) return '#E6A23C'
  return '#F56C6C'
}

// Cleanup on unmount
onUnmounted(() => {
  if (imageUrl.value) {
    URL.revokeObjectURL(imageUrl.value)
  }
})
</script>

<style scoped>
.image-recognition {
  width: 100%;
}

.upload-card {
  height: 100%;
  border: none;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-icon {
  font-size: 18px;
  color: #409eff;
}

.header-title {
  font-weight: 600;
  color: #303133;
}

.upload-area {
  margin-bottom: 20px;
  min-height: 300px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #fafafa;
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  padding: 40px 20px;
}

.upload-button-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  z-index: 10;
}

.main-upload-btn {
  background-color: #303133 !important;
  border-color: #303133 !important;
  color: white !important;
  padding: 16px 32px !important;
  font-size: 16px !important;
  height: auto !important;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.main-upload-btn:hover {
  background-color: #494a4d !important;
  border-color: #494a4d !important;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.main-upload-btn:active {
  transform: translateY(0);
}

.hidden-uploader {
  display: none !important;
}

.upload-hint {
  font-size: 12px;
  color: #909399;
}

.upload-btn {
  margin-top: 16px;
}

.upload-preview {
  position: relative;
  width: 100%;
  height: 200px;
  border-radius: 8px;
  overflow: hidden;
}

.preview-thumbnail {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.preview-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: white;
  opacity: 0;
  transition: opacity 0.3s ease;
  cursor: pointer;
}

.upload-preview:hover .preview-overlay {
  opacity: 1;
}

.preview-overlay .el-icon {
  font-size: 24px;
  margin-bottom: 8px;
}

.preview-container {
  position: relative;
  max-width: 100%;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.image-wrapper {
  position: relative;
  display: inline-block;
  width: 100%;
}

.preview-image {
  width: 100%;
  height: auto;
  display: block;
  max-height: 500px;
  object-fit: contain;
}

.overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.side-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
  height: 100%;
}

.result-card,
.tips-card {
  border: none;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.processing {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: #409eff;
}

.processing-icon {
  font-size: 32px;
  margin-bottom: 16px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.result-content {
  min-height: 200px;
}

.result-pass,
.result-reject,
.result-no-face {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 20px;
  border-radius: 8px;
}

.result-pass {
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border: 1px solid #bae6fd;
}

.result-reject {
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  border: 1px solid #fecaca;
}

.result-no-face {
  background: linear-gradient(135deg, #fefce8 0%, #fef3c7 100%);
  border: 1px solid #fde68a;
}

.result-icon {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 24px;
}

.result-pass .result-icon {
  background: #67c23a;
  color: white;
}

.result-reject .result-icon {
  background: #f56c6C;
  color: white;
}

.result-no-face .result-icon {
  background: #e6a23c;
  color: white;
}

.result-info {
  flex: 1;
}

.result-name {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.result-status {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #606266;
}

.confidence-bar {
  margin: 12px 0;
}

.confidence-label {
  font-size: 12px;
  color: #909399;
  display: block;
  margin-bottom: 4px;
}

.result-details {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
}

.timestamp {
  font-size: 12px;
  color: #909399;
}

.no-result {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: #909399;
}

.no-result-icon {
  font-size: 48px;
  margin-bottom: 16px;
  color: #c0c4cc;
}

.tips-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tip-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #606266;
}

.tip-item .el-icon {
  color: #67c23a;
  font-size: 16px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .upload-placeholder {
    padding: 30px 15px;
  }
  
  .upload-icon {
    font-size: 36px;
  }
  
  .result-pass,
  .result-reject,
  .result-no-face {
    flex-direction: column;
    text-align: center;
  }
  
  .result-icon {
    margin: 0 auto 12px auto;
  }
  
  .result-details {
    flex-direction: column;
    gap: 8px;
    align-items: flex-start;
  }
}
</style>

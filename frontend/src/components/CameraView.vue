<template>
  <div class="camera-view">
    <el-row :gutter="24">
      <el-col :lg="16" :md="24">
        <el-card class="video-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <div class="header-left">
                <el-icon class="header-icon"><VideoCamera /></el-icon>
                <span class="header-title">实时监控</span>
              </div>
              <div class="header-right">
                <el-tag :type="isCameraActive ? 'success' : 'info'" size="small">
                  {{ isCameraActive ? '运行中' : '已停止' }}
                </el-tag>
              </div>
            </div>
          </template>
          
          <div class="video-container">
            <video 
              ref="video" 
              autoplay 
              playsinline 
              muted
              :class="{ 'video-active': isCameraActive }"
            ></video>
            <canvas ref="canvas" class="overlay"></canvas>
            <div v-if="!isCameraActive" class="video-placeholder">
              <el-icon class="placeholder-icon"><VideoCamera /></el-icon>
              <p>摄像头未启动</p>
            </div>
          </div>
          
          <div class="control-panel">
            <el-button 
              type="primary" 
              size="large"
              @click="startCamera" 
              :disabled="isCameraActive"
              :loading="isStarting"
            >
              <el-icon><VideoPlay /></el-icon>
              启动摄像头
            </el-button>
            <el-button 
              type="danger" 
              size="large"
              @click="stopCamera" 
              :disabled="!isCameraActive"
            >
              <el-icon><VideoPause /></el-icon>
              停止摄像头
            </el-button>
            <el-button 
              type="info" 
              size="large"
              @click="switchToImage"
            >
              <el-icon><Picture /></el-icon>
              切换到图片
            </el-button>
          </div>
        </el-card>
      </el-col>
      
      <el-col :lg="8" :md="24">
        <div class="side-panel">
          <el-card class="status-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <el-icon class="header-icon"><DataAnalysis /></el-icon>
                <span class="header-title">识别结果</span>
              </div>
            </template>
            
            <div v-if="lastResult" class="result-content">
              <div v-if="lastResult.status === 'PASS'" class="result-pass">
                <div class="result-icon">
                  <el-icon><SuccessFilled /></el-icon>
                </div>
                <div class="result-info">
                  <h3 class="result-name">{{ lastResult.name }}</h3>
                  <p class="result-status">验证通过</p>
                  <div class="confidence-bar">
                    <span class="confidence-label">置信度</span>
                    <el-progress 
                      :percentage="(lastResult.confidence * 100).toFixed(1)"
                      :color="getConfidenceColor(lastResult.confidence)"
                      :stroke-width="8"
                    />
                  </div>
                </div>
              </div>
              
              <div v-else-if="lastResult.status === 'REJECT'" class="result-reject">
                <div class="result-icon">
                  <el-icon><CircleCloseFilled /></el-icon>
                </div>
                <div class="result-info">
                  <h3 class="result-name">未知人员</h3>
                  <p class="result-status">拒绝访问</p>
                  <el-tag type="danger" size="small">未授权</el-tag>
                </div>
              </div>
              
              <div v-else class="result-no-face">
                <div class="result-icon">
                  <el-icon><UserFilled /></el-icon>
                </div>
                <div class="result-info">
                  <h3 class="result-name">未检测到人脸</h3>
                  <p class="result-status">请调整位置</p>
                </div>
              </div>
            </div>
            
            <div v-else class="no-result">
              <el-icon class="no-result-icon"><Warning /></el-icon>
              <p>等待识别结果...</p>
            </div>
          </el-card>
          
          <el-card class="stats-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <el-icon class="header-icon"><TrendCharts /></el-icon>
                <span class="header-title">实时统计</span>
              </div>
            </template>
            
            <div class="stats-content">
              <div class="stat-item">
                <span class="stat-label">识别次数</span>
                <span class="stat-value">{{ recognitionCount }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">成功率</span>
                <span class="stat-value">{{ successRate }}%</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">运行时间</span>
                <span class="stat-value">{{ runningTime }}</span>
              </div>
            </div>
          </el-card>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { recognizeFace, getConfig } from '../api'
import { ElMessage } from 'element-plus'
import { 
  VideoCamera, 
  VideoPlay, 
  VideoPause, 
  Picture,
  DataAnalysis,
  SuccessFilled,
  CircleCloseFilled,
  UserFilled,
  Warning,
  TrendCharts
} from '@element-plus/icons-vue'

// 定义 emit
const emit = defineEmits(['mode-change'])

const video = ref(null)
const canvas = ref(null)
const isCameraActive = ref(false)
const isStarting = ref(false)
const lastResult = ref(null)
const recognitionCount = ref(0)
const successCount = ref(0)
const startTime = ref(null)

let stream = null
let intervalId = null
let config = { frame_interval_ms: 500 }

// 计算属性
const successRate = computed(() => {
  if (recognitionCount.value === 0) return 0
  return ((successCount.value / recognitionCount.value) * 100).toFixed(1)
})

const runningTime = computed(() => {
  if (!startTime.value) return '00:00:00'
  const now = Date.now()
  const diff = Math.floor((now - startTime.value) / 1000)
  const hours = Math.floor(diff / 3600)
  const minutes = Math.floor((diff % 3600) / 60)
  const seconds = diff % 60
  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
})

onMounted(async () => {
  try {
    const res = await getConfig()
    if (res) config = res
  } catch (e) {
    console.error('Failed to load config', e)
  }
})

onUnmounted(() => {
  stopCamera()
})

const startCamera = async () => {
  isStarting.value = true
  try {
    stream = await navigator.mediaDevices.getUserMedia({ 
      video: { 
        width: { ideal: 640 },
        height: { ideal: 480 }
      } 
    })
    
    if (!video.value) {
      throw new Error('Video element not found')
    }
    
    video.value.srcObject = stream
    isCameraActive.value = true
    startTime.value = Date.now()
    
    console.log('Stream assigned to video element')
    
    // Wait for video to actually have data
    video.value.onloadeddata = () => {
      console.log('Video data loaded, ready to play')
      console.log('Video dimensions:', video.value.videoWidth, 'x', video.value.videoHeight)
      
      // Use a longer delay to ensure everything is ready
      setTimeout(() => {
        initCanvasAndLoop()
      }, 500)
    }
    
    // Try to play the video
    try {
      await video.value.play()
      console.log('Video playback started')
    } catch (e) {
      console.error('Video play failed:', e)
    }
    
    ElMessage.success('摄像头启动成功')
  } catch (err) {
    console.error('Error accessing camera:', err)
    ElMessage.error('无法访问摄像头，请检查权限设置')
    isCameraActive.value = false
  } finally {
    isStarting.value = false
  }
}

const initCanvasAndLoop = () => {
  console.log('initCanvasAndLoop called')
  
  if (!video.value || !canvas.value) {
    console.error('Video or canvas not available')
    return
  }
  
  const width = video.value.videoWidth
  const height = video.value.videoHeight
  
  console.log('Checking video dimensions:', width, 'x', height)
  
  // Ensure video has valid dimensions
  if (width === 0 || height === 0) {
    console.warn('Video dimensions still not ready, retrying in 500ms...')
    setTimeout(() => {
      initCanvasAndLoop()
    }, 500)
    return
  }
  
  canvas.value.width = width
  canvas.value.height = height
  console.log('✓ Canvas initialized successfully:', canvas.value.width, 'x', canvas.value.height)
  
  startRecognitionLoop()
  console.log('✓ Recognition loop started successfully')
}

const stopCamera = () => {
  if (stream) {
    stream.getTracks().forEach(track => track.stop())
    stream = null
  }
  if (intervalId) {
    clearInterval(intervalId)
    intervalId = null
  }
  isCameraActive.value = false
  startTime.value = null
  
  // 添加 null 检查
  if (video.value) {
    video.value.srcObject = null
  }
  
  // Clear canvas
  if (canvas.value) {
    const ctx = canvas.value.getContext('2d')
    ctx.clearRect(0, 0, canvas.value.width, canvas.value.height)
  }
  
  ElMessage.info('摄像头已停止')
}

const switchToImage = () => {
  stopCamera()
  emit('mode-change', 'image')
}

const startRecognitionLoop = () => {
  intervalId = setInterval(captureAndRecognize, config.frame_interval_ms)
}

const captureAndRecognize = async () => {
  if (!video.value || !canvas.value || !isCameraActive.value) return
  
  // Ensure video has enough data
  if (video.value.readyState < 2) return

  const captureCanvas = document.createElement('canvas')
  captureCanvas.width = video.value.videoWidth
  captureCanvas.height = video.value.videoHeight
  captureCanvas.getContext('2d').drawImage(video.value, 0, 0)
  
  captureCanvas.toBlob(async (blob) => {
    if (!blob) return
    
    const formData = new FormData()
    formData.append('file', blob, 'capture.jpg')
    
    try {
      const res = await recognizeFace(formData)
      lastResult.value = res
      recognitionCount.value++
      
      if (res.status === 'PASS') {
        successCount.value++
      }
      
      drawResult(res)
    } catch (e) {
      console.error('Recognition error', e)
    }
  }, 'image/jpeg')
}

const drawResult = (result) => {
  const ctx = canvas.value.getContext('2d')
  ctx.clearRect(0, 0, canvas.value.width, canvas.value.height)
  
  if (result.status === 'NO_FACE' || !result.box) return
  
  const [x, y, w, h] = result.box
  
  // Draw bounding box
  ctx.lineWidth = 3
  ctx.strokeStyle = result.status === 'PASS' ? '#67C23A' : '#F56C6C'
  ctx.strokeRect(x, y, w, h)
  
  // Draw label background
  ctx.font = 'bold 16px Arial'
  const text = result.name || '未知'
  const textWidth = ctx.measureText(text).width
  
  ctx.fillStyle = result.status === 'PASS' ? '#67C23A' : '#F56C6C'
  ctx.fillRect(x, y - 25, textWidth + 10, 25)
  
  // Draw label text
  ctx.fillStyle = 'white'
  ctx.fillText(text, x + 5, y - 8)
}

const getConfidenceColor = (confidence) => {
  if (confidence >= 0.8) return '#67C23A'
  if (confidence >= 0.6) return '#E6A23C'
  return '#F56C6C'
}
</script>

<style scoped>
.camera-view {
  width: 100%;
}

.video-card {
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

.video-container {
  position: relative;
  width: 100%;
  aspect-ratio: 4/3;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 20px;
}

video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.video-active {
  display: block;
}

.overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.video-placeholder {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  color: #909399;
}

.placeholder-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.control-panel {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
}

.side-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
  height: 100%;
}

.status-card,
.stats-card {
  border: none;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
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
  margin-top: 12px;
}

.confidence-label {
  font-size: 12px;
  color: #909399;
  display: block;
  margin-bottom: 4px;
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

.stats-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.stat-item:last-child {
  border-bottom: none;
}

.stat-label {
  font-size: 14px;
  color: #606266;
}

.stat-value {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .control-panel {
    flex-direction: column;
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
}
</style>

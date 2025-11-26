<template>
  <div class="dashboard">
    <el-row :gutter="24">
      <el-col :span="24">
        <div class="dashboard-header-card">
          <div class="header-content">
            <div class="header-left">
              <h1 class="dashboard-title">
                <el-icon><VideoCamera /></el-icon>
                人脸识别监控中心
              </h1>
              <p class="dashboard-subtitle">智能门禁管理系统 - 实时监控与身份验证</p>
            </div>
            <div class="header-right">
              <el-tag :type="systemStatus === '在线' ? 'success' : 'danger'" effect="dark" class="status-tag">
                <el-icon><Connection /></el-icon>
                {{ systemStatus }}
              </el-tag>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="24" class="main-content">
      <el-col :lg="16" :xl="17">
        <el-card class="mode-card" shadow="never">
          <div class="mode-header">
            <div class="mode-title">
              <h3>识别模式</h3>
              <span class="mode-desc">选择实时摄像头或上传图片进行识别</span>
            </div>
            <el-radio-group v-model="mode" size="default">
              <el-radio-button label="camera">
                <el-icon><VideoCamera /></el-icon>
                <span>实时监控</span>
              </el-radio-button>
              <el-radio-button label="image">
                <el-icon><Picture /></el-icon>
                <span>图片识别</span>
              </el-radio-button>
            </el-radio-group>
          </div>
          
          <div class="content-area">
            <transition name="fade" mode="out-in">
              <div :key="mode" class="view-container">
                <CameraView v-if="mode === 'camera'" @mode-change="handleModeChange" />
                <ImageRecognition v-else-if="mode === 'image'" @mode-change="handleModeChange" />
              </div>
            </transition>
          </div>
        </el-card>
      </el-col>
      
      <el-col :lg="8" :xl="7">
        <div class="side-panel">
          <el-card class="stats-card" shadow="never">
            <template #header>
              <div class="card-header">
                <span class="header-title">今日概览</span>
                <el-tag size="small" effect="plain">{{ new Date().toLocaleDateString() }}</el-tag>
              </div>
            </template>
            <div class="stats-grid">
              <div class="stat-box">
                <div class="stat-icon primary-bg">
                  <el-icon><User /></el-icon>
                </div>
                <div class="stat-info">
                  <span class="stat-value">{{ recognitionCount }}</span>
                  <span class="stat-label">识别总数</span>
                </div>
              </div>
              <div class="stat-box">
                <div class="stat-icon success-bg">
                  <el-icon><Check /></el-icon>
                </div>
                <div class="stat-info">
                  <span class="stat-value">{{ successRate }}%</span>
                  <span class="stat-label">通过率</span>
                </div>
              </div>
            </div>
          </el-card>

          <el-card class="logs-card" shadow="never">
            <template #header>
              <div class="card-header">
                <span class="header-title">最近活动</span>
                <el-button link type="primary" size="small" @click="$router.push('/admin')">查看全部</el-button>
              </div>
            </template>
            <div class="recent-logs">
              <el-empty v-if="!recentLogs.length" description="暂无活动记录" :image-size="60" />
              <div v-else class="log-list">
                <!-- 这里可以后续添加实时日志列表 -->
                <div class="log-placeholder">
                  日志功能开发中...
                </div>
              </div>
            </div>
          </el-card>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import CameraView from '../components/CameraView.vue'
import ImageRecognition from '../components/ImageRecognition.vue'
import { VideoCamera, Picture, Connection, User, Check } from '@element-plus/icons-vue'

const mode = ref('camera')
const systemStatus = ref('在线')
const recognitionCount = ref(0)
const successCount = ref(0)
const recentLogs = ref([])

const handleModeChange = (newMode) => {
  mode.value = newMode
}

const successRate = computed(() => {
  if (recognitionCount.value === 0) return 0
  return ((successCount.value / recognitionCount.value) * 100).toFixed(1)
})
</script>

<style scoped>
.dashboard {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.dashboard-header-card {
  background: white;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.dashboard-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
}

.dashboard-subtitle {
  margin: 0;
  color: #6b7280;
  font-size: 14px;
}

.status-tag {
  padding: 8px 16px;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.mode-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.mode-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.mode-title h3 {
  margin: 0 0 4px 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.mode-desc {
  font-size: 13px;
  color: #909399;
}

.content-area {
  min-height: 600px;
}

.side-panel {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.stat-box {
  background: #f8fafc;
  border-radius: 8px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.stat-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: white;
}

.primary-bg { background: #409eff; }
.success-bg { background: #67c23a; }

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: #303133;
}

.stat-label {
  font-size: 12px;
  color: #909399;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  font-weight: 600;
  font-size: 16px;
}

.recent-logs {
  min-height: 300px;
}

.log-placeholder {
  text-align: center;
  color: #909399;
  padding: 20px;
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>

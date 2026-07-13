<template>
  <view class="history-page">
    <view class="ambient-background">
      <view class="orb orb-gold"></view>
      <view class="orb orb-champagne"></view>
    </view>

    <view class="page-header animate-fade-in-up" style="animation-delay: 0s;">
      <view class="header-top">
        <view>
          <text class="page-title">创作时光轴</text>
          <text class="page-subtitle">记录每一次修复的痕迹</text>
        </view>
        <view class="header-actions">
          <view v-if="histories.length > 0 && !isSelectMode" class="action-btn glass-btn float-hover" @tap="enterSelectMode">
            <text class="action-text">选择</text>
          </view>
        </view>
      </view>
    </view>

    <view v-if="isSelectMode" class="select-bar-wrapper animate-fade-in-up">
      <view class="select-bar glass-panel">
        <view class="select-info">
          <text class="select-count">{{ selectedHistoryIds.length }}/{{ histories.length }} 已选择</text>
          <view class="select-all-btn float-hover" @tap="toggleSelectAll">
            <text>{{ selectedHistoryIds.length === histories.length ? '取消全选' : '全选' }}</text>
          </view>
        </view>
        <view class="select-actions">
          <view class="cancel-btn float-hover" @tap="exitSelectMode"><text>取消</text></view>
          <view class="delete-btn float-hover" :class="{ disabled: selectedHistoryIds.length === 0 }" @tap="batchDelete">
            <text>删除({{ selectedHistoryIds.length }})</text>
          </view>
        </view>
      </view>
    </view>

    <view v-if="processingTasks.length > 0" class="processing-section animate-fade-in-up" style="animation-delay: 0.1s;">
      <view v-for="task in processingTasks" :key="task.task_id" class="processing-card glass-panel">
        <view class="processing-indicator">
          <view class="pulse-dot"></view>
        </view>
        <view class="processing-info">
          <text class="processing-name">{{ getOperationName(task.operation_type) }}</text>
          <text class="processing-status">AI 时光引擎运转中...</text>
        </view>
      </view>
    </view>

    <!-- 时光轴：流光轨迹列表 -->
    <view class="timeline-track">
      <view
        v-for="(history, index) in histories"
        :key="history.id"
        class="timeline-item animate-fade-in-up"
        :style="{ animationDelay: `${0.15 + (index % 10) * 0.06}s` }"
      >
        <view class="timeline-node" :class="{ 'node-selected': selectedHistoryIds.includes(history.id) }">
          <view class="node-dot"></view>
        </view>

        <view
          class="history-card glass-panel float-hover"
          :class="{ selected: selectedHistoryIds.includes(history.id) }"
          @tap="onHistoryTap(history)"
        >
          <view v-if="isSelectMode" class="check-box" :class="{ checked: selectedHistoryIds.includes(history.id) }">
            <text v-if="selectedHistoryIds.includes(history.id)" class="check-mark">✓</text>
          </view>

          <view class="history-thumb">
            <image v-if="history.media_type === 'image'" class="thumb-img" :src="history.result_url || history.input_url" mode="aspectFill" lazy-load />
            <view v-else-if="history.media_type === 'audio'" class="thumb-placeholder glass-inner">
              <text class="placeholder-icon">🎙️</text>
            </view>
            <view v-else-if="history.media_type === 'video'" class="thumb-placeholder glass-inner">
              <text class="placeholder-icon">🎬</text>
            </view>
            <view v-else class="thumb-placeholder glass-inner">
              <text class="placeholder-icon">📄</text>
            </view>
          </view>

          <view class="history-info">
            <view class="info-header">
              <text class="operation-tag">{{ getOperationName(history.operation_type) }}</text>
              <text class="media-type-tag">{{ getMediaTypeName(history.media_type) }}</text>
            </view>
            <text class="history-date">{{ formatDate(history.created_at) }}</text>
          </view>

          <view v-if="!isSelectMode" class="view-btn">
            <text class="view-arrow">→</text>
          </view>
        </view>
      </view>
    </view>

    <view v-if="hasMore && histories.length > 0" class="load-more" @tap="loadMoreHistories">
      <text class="load-more-text">{{ isLoadingMore ? '时光回溯中...' : '加载更多痕迹' }}</text>
    </view>

    <view v-if="histories.length === 0 && !isLoading" class="empty-state animate-fade-in-up" style="animation-delay: 0.3s;">
      <view class="empty-glass-icon float-breathing">
        <text class="empty-emoji">🕐</text>
      </view>
      <text class="empty-text">暂无修复记录</text>
      <text class="empty-hint">去修复工坊开始第一次修复吧</text>
    </view>

    <view v-if="selectedHistory" class="detail-popup" @tap="closeDetail">
      <view class="detail-content" @tap.stop>
        
        <view v-if="selectedHistory.media_type === 'image'" class="detail-interactive-compare">
          
          <view class="image-stack-container">
            <image class="img-layer img-original" :src="selectedHistory.input_url" mode="aspectFit" />
            <image class="img-layer img-repaired" :class="{ 'fade-out': isShowingOriginal }" :src="selectedHistory.result_url" mode="aspectFit" />
            
            <view class="status-badge glass-panel-light">
              <text class="badge-dot" :class="{ 'dot-original': isShowingOriginal }"></text>
              <text>{{ isShowingOriginal ? '原图' : '修复后' }}</text>
            </view>
          </view>

          <view class="compare-control">
            <view 
              class="compare-btn float-hover"
              @touchstart="startCompare"
              @touchend="stopCompare"
              @touchcancel="stopCompare"
              @mousedown="startCompare"
              @mouseup="stopCompare"
              @mouseleave="stopCompare"
            >
              <view class="compare-icon-wrap"><text class="c-icon">✨</text></view>
              <text class="compare-text">长按对比原图</text>
            </view>
          </view>

        </view>
        <view v-else-if="selectedHistory.media_type === 'audio'" class="detail-audio">
          <view class="audio-player-card float-hover" @tap="playAudio">
            <view class="audio-icon-wrap" :class="{ 'is-playing': isPlaying }">
              <text class="audio-icon">{{ isPlaying ? '⏸' : '▶️' }}</text>
            </view>
            <view class="audio-info">
              <text class="audio-title">留音结果</text>
              <text class="audio-status">{{ isPlaying ? '播放中...' : '点击播放' }}</text>
            </view>
          </view>
        </view>

        <view v-else-if="selectedHistory.media_type === 'video'" class="detail-video">
          <video v-if="selectedHistory.result_url" :src="selectedHistory.result_url" class="video-player" controls />
        </view>

        <view class="detail-info glass-panel-light">
          <view class="detail-row">
            <text class="detail-label">修复类型</text>
            <text class="detail-value gold-text">{{ getOperationName(selectedHistory.operation_type) }}</text>
          </view>
          <view class="detail-row">
            <text class="detail-label">记录时间</text>
            <text class="detail-value">{{ formatDate(selectedHistory.created_at) }}</text>
          </view>
        </view>

        <view class="detail-actions">
          <view class="detail-btn repair-btn float-hover" @tap="navigateToModule(selectedHistory)">
            <text>跳转至修复工坊</text>
          </view>
          <view class="detail-btn download-btn float-hover" @tap="downloadResult">
            <text>保存到相册</text>
          </view>
          <view class="detail-btn delete-detail-btn float-hover" @tap="deleteHistory(selectedHistory)">
            <text>删除痕迹</text>
          </view>
        </view>

        <view class="close-btn float-hover" @tap="closeDetail">
          <text>✕</text>
        </view>
      </view>
    </view>

    <!-- 自定义确认删除弹窗（置顶，解决 uni.showModal 被遮挡问题） -->
    <view v-if="confirmDialog.visible" class="confirm-overlay" @tap="cancelConfirm">
      <view class="confirm-dialog glass-panel" @tap.stop>
        <view class="confirm-icon-wrap"><text class="confirm-icon">⚠️</text></view>
        <text class="confirm-title">{{ confirmDialog.title }}</text>
        <text class="confirm-content">{{ confirmDialog.message }}</text>
        <view class="confirm-actions">
          <view class="confirm-btn confirm-cancel float-hover" @tap="cancelConfirm">
            <text>取消</text>
          </view>
          <view class="confirm-btn confirm-ok float-hover" @tap="executeConfirm">
            <text>确认删除</text>
          </view>
        </view>
      </view>
    </view>

    <view style="height: 180rpx;"></view>

    <CustomTabBar :selected="2" />
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { onShow, onHide } from '@dcloudio/uni-app'
import CustomTabBar from '@/components/CustomTabBar.vue'
import { get, del, getToken } from '@/utils/request'

interface HistoryItem {
  id: number
  operation_type: string
  media_type: string
  input_path: string
  result_path: string
  input_url: string
  result_url: string
  created_at: string
}

const histories = ref<HistoryItem[]>([])
const selectedHistory = ref<HistoryItem | null>(null)
const isLoading = ref(false)
const isLoadingMore = ref(false)
const hasMore = ref(true)
const currentPage = ref(0)
const pageSize = 20
const isSelectMode = ref(false)
const selectedHistoryIds = ref<number[]>([])
const isPlaying = ref(false)
let audioInstance: UniApp.InnerAudioContext | null = null

// 新增：控制按压对比的状态
const isShowingOriginal = ref(false)

const startCompare = () => { isShowingOriginal.value = true }
const stopCompare = () => { isShowingOriginal.value = false }

const processingTasks = ref<Array<{
  id: string
  operation_type: string
  task_id: string
  status: string
}>>([])

let pollingTimer: ReturnType<typeof setInterval> | null = null

// 自定义确认弹窗状态
const confirmDialog = ref({ visible: false, title: '', message: '', onConfirm: null as (() => void) | null })
const showConfirm = (title: string, message: string, onConfirm: () => void) => {
  confirmDialog.value = { visible: true, title, message, onConfirm }
}
const cancelConfirm = () => {
  confirmDialog.value = { visible: false, title: '', message: '', onConfirm: null }
}
const executeConfirm = () => {
  if (confirmDialog.value.onConfirm) {
    confirmDialog.value.onConfirm()
  }
  cancelConfirm()
}

const STATIC_BASE = 'http://localhost:8000'

const getFullUrl = (path: string | undefined): string => {
  if (!path) return ''
  if (path.startsWith('http')) return path
  let cleanPath = path.replace(/\\/g, '/')
  cleanPath = cleanPath.startsWith('/') ? cleanPath.substring(1) : cleanPath
  while (cleanPath.startsWith('static/static/')) {
    cleanPath = cleanPath.replace('static/static/', 'static/')
  }
  if (!cleanPath.startsWith('static/')) {
    cleanPath = `static/${cleanPath}`
  }
  return `${STATIC_BASE}/${cleanPath}`
}

const operationTypeMap: Record<string, string> = {
  'dustless': '拂尘修复',
  'colorize': '流光上色',
  'clarity': '清影清晰',
  'trueface': '真容修复',
  'tts': '留音 (文字)',
  'voice_clone': '留音 (克隆)',
  'voice': '留音',
  'live_portrait': '灵动人像',
  'liveportrait': '灵动人像',
  'liveportrait_video': '灵动视频',
  'time_engine': '时光引擎'
}

const getOperationName = (type: string): string => operationTypeMap[type] || type

const getMediaTypeName = (type: string): string => {
  const map: Record<string, string> = { 'image': '影像', 'audio': '声音', 'video': '动态' }
  return map[type] || type
}

// 操作类型到模块ID的映射（对应 module.vue 中 moduleConfigs 的 key）
const operationToModuleMap: Record<string, string> = {
  'dustless': 'dustless',
  'colorize': 'liuguang',
  'clarity': 'qingying',
  'trueface': 'zhenrong',
  'tts': 'voice',
  'voice_clone': 'voice',
  'voice': 'voice',
  'live_portrait': 'live_portrait',
  'liveportrait': 'live_portrait',
  'liveportrait_video': 'live_portrait',
  'time_engine': 'time_engine'
}

const getModuleIdFromHistory = (history: HistoryItem): string => {
  return operationToModuleMap[history.operation_type] || 'dustless'
}

// 跳转到对应模块的修复工坊，并显示修复结果
const navigateToModule = (history: HistoryItem) => {
  const moduleId = getModuleIdFromHistory(history)
  closeDetail()
  uni.navigateTo({
    url: `/pages/workshop/module?id=${moduleId}&history_id=${history.id}`
  })
}

const formatDate = (dateString: string): string => {
  try {
    const date = new Date(dateString)
    return date.toLocaleString('zh-CN', {
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit'
    })
  } catch { return dateString }
}

const loadHistories = async (loadMore = false) => {
  if (loadMore) {
    isLoadingMore.value = true
  } else {
    isLoading.value = true
    currentPage.value = 0
    histories.value = []
  }
  try {
    const skip = currentPage.value * pageSize
    const data = await get<any[]>('/workshop/histories', { skip, limit: pageSize })
    console.log('[创作时光轴] API 返回数据条数:', Array.isArray(data) ? data.length : '非数组', data)
    if (!Array.isArray(data)) {
      console.error('[创作时光轴] API 返回非数组数据:', data)
      histories.value = []
      hasMore.value = false
      return
    }
    const mapped = data.map(h => ({
      ...h,
      input_url: getFullUrl(h.input_path),
      result_url: getFullUrl(h.result_path)
    }))
    if (loadMore) {
      histories.value = [...histories.value, ...mapped]
    } else {
      histories.value = mapped
    }
    hasMore.value = data.length === pageSize
  } catch (error) {
    console.error('加载历史记录失败', error)
    uni.showToast({ title: '加载历史失败，请重试', icon: 'none' })
  } finally {
    isLoading.value = false
    isLoadingMore.value = false
  }
}

const loadMoreHistories = async () => {
  if (isLoadingMore.value || !hasMore.value) return
  currentPage.value += 1
  await loadHistories(true)
}

const onHistoryTap = (history: HistoryItem) => {
  if (isSelectMode.value) {
    toggleSelect(history.id)
  } else {
    viewDetail(history)
  }
}

const viewDetail = (history: HistoryItem) => {
  selectedHistory.value = history
  isShowingOriginal.value = false // 重置对比状态
}

const closeDetail = () => {
  selectedHistory.value = null
  stopAudio()
}

const stopAudio = () => {
  if (audioInstance) {
    audioInstance.stop()
    audioInstance.destroy()
    audioInstance = null
  }
  isPlaying.value = false
}

const playAudio = () => {
  if (!selectedHistory.value?.result_url) return
  if (isPlaying.value) {
    stopAudio()
    return
  }
  stopAudio()
  isPlaying.value = true
  uni.showToast({ title: '流光运转中', icon: 'none' })
  audioInstance = uni.createInnerAudioContext()
  audioInstance.src = selectedHistory.value.result_url
  audioInstance.play()
  audioInstance.onEnded(() => { isPlaying.value = false; audioInstance = null })
  audioInstance.onError(() => { isPlaying.value = false; audioInstance = null })
}

const downloadResult = () => {
  if (!selectedHistory.value?.result_url) {
    uni.showToast({ title: '无法获取资源', icon: 'none' })
    return
  }
  // H5 端 uni.downloadFile 会因 CORS 无法读取 Content-Disposition 头而报错
  // 直接使用 uni.request + arraybuffer 方案
  uni.showLoading({ title: '下载中...' })
  uni.request({
    url: selectedHistory.value.result_url,
    responseType: 'arraybuffer',
    success: (reqRes) => {
      uni.hideLoading()
      if (reqRes.statusCode === 200 && reqRes.data) {
        const buffer = reqRes.data as ArrayBuffer
        if (buffer.byteLength === 0) {
          uni.showToast({ title: '下载的文件为空', icon: 'none' })
          return
        }
        // H5 平台：uni.getFileSystemManager 不存在，用 Blob 下载方式
        // #ifdef H5
        try {
          const blob = new Blob([buffer], { type: 'image/jpeg' })
          const blobUrl = URL.createObjectURL(blob)
          const link = document.createElement('a')
          link.href = blobUrl
          link.download = `time_trace_${Date.now()}.jpg`
          link.style.display = 'none'
          document.body.appendChild(link)
          link.click()
          setTimeout(() => {
            document.body.removeChild(link)
            URL.revokeObjectURL(blobUrl)
          }, 100)
          uni.showToast({ title: '图片已下载', icon: 'success' })
        } catch (e: any) {
          uni.showToast({ title: '保存失败', icon: 'none' })
        }
        // #endif
        // #ifndef H5
        const fs = uni.getFileSystemManager()
        const tempPath = `${uni.env.USER_DATA_PATH}/save_${Date.now()}.jpg`
        fs.writeFile({
          filePath: tempPath,
          data: buffer,
          success: () => {
            uni.saveImageToPhotosAlbum({
              filePath: tempPath,
              success: () => uni.showToast({ title: '已珍藏至相册', icon: 'success' }),
              fail: () => uni.showToast({ title: '保存失败，请检查权限', icon: 'none' })
            })
          },
          fail: () => uni.showToast({ title: '文件写入失败', icon: 'none' })
        })
        // #endif
      } else {
        uni.showToast({ title: '下载失败', icon: 'none' })
      }
    },
    fail: () => {
      uni.hideLoading()
      uni.showToast({ title: '下载失败，请检查网络', icon: 'none' })
    }
  })
}

const deleteHistory = (history: HistoryItem) => {
  showConfirm(
    '抹除痕迹',
    `确定要删除"${getOperationName(history.operation_type)}"的记录吗？`,
    async () => {
      try {
        await del(`/workshop/histories/${history.id}`)
        histories.value = histories.value.filter(h => h.id !== history.id)
        if (selectedHistory.value?.id === history.id) {
          selectedHistory.value = null
        }
        uni.showToast({ title: '痕迹已抹除', icon: 'success' })
      } catch (error) {
        uni.showToast({ title: '抹除失败', icon: 'none' })
      }
    }
  )
}

const enterSelectMode = () => { isSelectMode.value = true }
const exitSelectMode = () => { isSelectMode.value = false; selectedHistoryIds.value = [] }
const toggleSelect = (id: number) => {
  const index = selectedHistoryIds.value.indexOf(id)
  if (index === -1) selectedHistoryIds.value.push(id)
  else selectedHistoryIds.value.splice(index, 1)
}
const toggleSelectAll = () => {
  selectedHistoryIds.value = selectedHistoryIds.value.length === histories.value.length
    ? [] : histories.value.map(h => h.id)
}
const batchDelete = async () => {
  if (selectedHistoryIds.value.length === 0) return
  showConfirm(
    '批量抹除',
    `确定要删除选中的 ${selectedHistoryIds.value.length} 条记录吗？`,
    async () => {
      try {
        for (const id of selectedHistoryIds.value) {
          await del(`/workshop/histories/${id}`)
        }
        histories.value = histories.value.filter(h => !selectedHistoryIds.value.includes(h.id))
        exitSelectMode()
        uni.showToast({ title: '清理成功', icon: 'success' })
      } catch (error) {
        uni.showToast({ title: '清理失败', icon: 'none' })
      }
    }
  )
}

const startPolling = () => {
  if (pollingTimer) return
  pollingTimer = setInterval(async () => {
    if (processingTasks.value.length === 0) return
    for (const task of processingTasks.value) {
      if (task.status === 'processing') {
        try {
          const status = await get<any>(`/workshop/tasks/${task.task_id}/status`)
          if (status.status === 'completed') {
            task.status = 'completed'
            processingTasks.value = processingTasks.value.filter(t => t.task_id !== task.task_id)
            loadHistories()
          } else if (status.status === 'failed') {
            task.status = 'failed'
            processingTasks.value = processingTasks.value.filter(t => t.task_id !== task.task_id)
          }
        } catch (e) { /* ignore */ }
      }
    }
  }, 3000)
}

onMounted(() => {
  const token = getToken()
  if (!token) {
    uni.reLaunch({ url: '/pages/login/login' })
    return
  }
  loadHistories()
  startPolling()
})

// 每次页面显示时检测是否有待刷新的记录并重新加载
onShow(() => {
  try {
    const pendingRefresh = uni.getStorageSync('time_trace_pending_refresh')
    if (pendingRefresh) {
      console.log('[创作时光轴] 检测到待刷新标记，重新加载历史记录')
      uni.removeStorageSync('time_trace_pending_refresh')
      loadHistories()
    }
  } catch (e) {
    // 忽略存储读取错误
  }
  startPolling()
})

onHide(() => {
  // 页面隐藏时暂停轮询
  if (pollingTimer) {
    clearInterval(pollingTimer)
    pollingTimer = null
  }
})

onUnmounted(() => {
  if (pollingTimer) clearInterval(pollingTimer)
  stopAudio()
})
</script>

<style lang="scss" scoped>
/* ================= 核心动画与环境 ================= */
@keyframes fadeInUp {
  0% { opacity: 0; transform: translateY(40rpx) scale(0.98); }
  100% { opacity: 1; transform: translateY(0) scale(1); }
}

@keyframes orbDrift {
  0% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(40rpx, -30rpx) scale(1.1); }
  100% { transform: translate(0, 0) scale(1); }
}

@keyframes nodePulse {
  0%, 100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(212, 175, 55, 0.4); }
  50% { transform: scale(1.15); box-shadow: 0 0 24rpx 8rpx rgba(212, 175, 55, 0.2); }
}

@keyframes trailFlow {
  0% { opacity: 0.3; }
  50% { opacity: 0.8; }
  100% { opacity: 0.3; }
}

@keyframes cardJelly {
  0% { transform: scale(1); }
  50% { transform: scale(0.97); }
  100% { transform: scale(1); }
}

.animate-fade-in-up {
  opacity: 0;
  animation: fadeInUp 0.6s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
}

.float-hover {
  transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.3s ease;
  &:active { animation: cardJelly 0.35s cubic-bezier(0.34, 1.56, 0.64, 1); box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.05); }
}

.ambient-background {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: var(--bg-elegant, #FAF8F5); z-index: -1; overflow: hidden;
}
.orb { position: absolute; border-radius: 50%; filter: blur(90px); opacity: 0.4; animation: orbDrift 15s ease-in-out infinite; }
.orb-gold { width: 600rpx; height: 600rpx; background: rgba(212, 175, 55, 0.2); top: -10%; left: -20%; }
.orb-champagne { width: 700rpx; height: 700rpx; background: rgba(242, 169, 127, 0.15); bottom: 10%; right: -20%; animation-delay: -5s; }

/* 基础结构 */
.history-page { min-height: 100vh; padding: 0 40rpx; }

.page-header {
  padding: 40rpx 0 32rpx;
  .header-top { display: flex; justify-content: space-between; align-items: flex-start; }
  .page-title { display: block; font-size: 60rpx; font-weight: 800; color: var(--text-main, #3D352B); letter-spacing: 2rpx; }
  .page-subtitle { display: block; font-size: 26rpx; color: var(--text-muted, #A39B90); margin-top: 16rpx; font-weight: 500; }
}

/* 玻璃控件通用类 */
.glass-btn {
  padding: 16rpx 40rpx; border-radius: 40rpx;
  background: rgba(255, 255, 255, 0.5); backdrop-filter: blur(16px);
  border: 1rpx solid rgba(255, 255, 255, 0.9); box-shadow: 0 8rpx 24rpx rgba(0,0,0,0.03);
  .action-text { font-size: 26rpx; color: var(--gold-dark, #B58D1F); font-weight: 800; }
}

.glass-panel {
  background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px);
  border: 1rpx solid rgba(255, 255, 255, 0.85);
  box-shadow: 0 16rpx 40rpx rgba(44, 36, 23, 0.04), inset 0 4rpx 8rpx rgba(255, 255, 255, 0.5);
  border-radius: 40rpx;
}

.glass-panel-light {
  background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(12px);
  border-radius: 24rpx; border: 1rpx solid #FFFFFF; box-shadow: 0 8rpx 24rpx rgba(0,0,0,0.03);
}

/* ================= 批量选择 & 任务状态 ================= */
.select-bar-wrapper { margin-bottom: 32rpx; }
.select-bar {
  padding: 24rpx 32rpx;
  .select-info {
    display: flex; justify-content: space-between; align-items: center; margin-bottom: 24rpx;
    .select-count { font-size: 30rpx; color: #5A4A32; font-weight: 800; }
    .select-all-btn { padding: 10rpx 28rpx; background: rgba(255, 255, 255, 0.8); border-radius: 30rpx; font-size: 24rpx; color: var(--gold-main); font-weight: 800; }
  }
  .select-actions {
    display: flex; gap: 24rpx;
    .cancel-btn { flex: 1; padding: 20rpx 0; text-align: center; background: rgba(255,255,255,0.7); border-radius: 28rpx; font-size: 28rpx; color: #8C7A5A; font-weight: 700; border: 1px solid #FFF; }
    .delete-btn { flex: 1; padding: 20rpx 0; text-align: center; background: linear-gradient(135deg, #FF7676, #EE5A24); border-radius: 28rpx; font-size: 28rpx; color: #fff; font-weight: 800; box-shadow: 0 8rpx 24rpx rgba(238, 90, 36, 0.2); }
  }
}

.processing-section { margin-bottom: 32rpx; }
.processing-card {
  display: flex; align-items: center; padding: 24rpx 32rpx;
  .processing-indicator { margin-right: 24rpx; .pulse-dot { width: 20rpx; height: 20rpx; background: var(--gold-main); border-radius: 50%; animation: nodePulse 1.5s infinite; } }
  .processing-info {
    .processing-name { display: block; font-size: 30rpx; color: #5A4A32; font-weight: 800; }
    .processing-status { display: block; font-size: 24rpx; color: var(--gold-dark); margin-top: 6rpx; font-weight: 500; }
  }
}

/* ================= 时光轴：流光轨迹 ================= */
.timeline-track {
  position: relative;
  padding-left: 60rpx;
  display: flex; flex-direction: column; gap: 28rpx;

  /* 流光轨迹线 */
  &::before {
    content: '';
    position: absolute; left: 22rpx; top: 10rpx; bottom: 10rpx;
    width: 4rpx;
    background: linear-gradient(180deg,
      rgba(212, 175, 55, 0.6),
      rgba(242, 169, 127, 0.5) 50%,
      rgba(212, 175, 55, 0.2)
    );
    border-radius: 4rpx;
    animation: trailFlow 3s ease-in-out infinite;
  }
}

.timeline-item {
  position: relative;
  display: flex; align-items: stretch;
}

/* 流光节点 */
.timeline-node {
  position: absolute; left: -60rpx; top: 50%;
  transform: translateY(-50%);
  width: 48rpx; height: 48rpx;
  display: flex; align-items: center; justify-content: center;
  z-index: 2;

  .node-dot {
    width: 18rpx; height: 18rpx;
    border-radius: 50%;
    background: linear-gradient(135deg, #D4AF37, #F2A97F);
    box-shadow: 0 0 12rpx 4rpx rgba(212, 175, 55, 0.3);
    animation: nodePulse 2s ease-in-out infinite;
    transition: all 0.3s ease;
  }

  &.node-selected .node-dot {
    width: 24rpx; height: 24rpx;
    box-shadow: 0 0 24rpx 8rpx rgba(212, 175, 55, 0.5);
    background: linear-gradient(135deg, #D4AF37, #FFC107);
  }
}

/* 时光卡片 */
.history-card {
  display: flex; align-items: center; padding: 24rpx 28rpx; position: relative;
  flex: 1; min-height: 140rpx;
  border-radius: 36rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.9);
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);

  &.selected {
    box-shadow: 0 0 0 4rpx rgba(212, 175, 55, 0.4), 0 16rpx 40rpx rgba(212, 175, 55, 0.1);
    border-color: rgba(212, 175, 55, 0.3);
  }

  .check-box {
    position: absolute; top: 16rpx; left: 16rpx; width: 40rpx; height: 40rpx; border-radius: 50%;
    background: rgba(255, 255, 255, 0.9); border: 2rpx solid #E8DCC8;
    display: flex; align-items: center; justify-content: center; z-index: 10;
    &.checked { background: linear-gradient(135deg, #D4AF37, #F2A97F); border-color: #D4AF37; }
    .check-mark { color: #FFF; font-size: 22rpx; font-weight: 800; }
  }

  .history-thumb {
    width: 112rpx; height: 112rpx;
    border-radius: 28rpx; overflow: hidden; margin-right: 24rpx;
    flex-shrink: 0;
    box-shadow: 0 8rpx 20rpx rgba(0,0,0,0.04);
    border: 1rpx solid rgba(255, 255, 255, 0.5);
    position: relative;

    &::after {
      content: '';
      position: absolute; inset: 0;
      border-radius: 28rpx;
      box-shadow: inset 0 2rpx 4rpx rgba(255,255,255,0.3);
      pointer-events: none;
    }

    .thumb-img { width: 100%; height: 100%; display: block; }
    .thumb-placeholder {
      width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;
      background: linear-gradient(135deg, #FDF8EF, #FFFFFF);
      .placeholder-icon { font-size: 44rpx; }
    }
  }

  .history-info {
    flex: 1; min-width: 0;
    .info-header { display: flex; align-items: center; gap: 12rpx; margin-bottom: 10rpx; }
    .operation-tag {
      font-size: 20rpx; padding: 4rpx 14rpx; border-radius: 14rpx; font-weight: 700;
      background: linear-gradient(135deg, rgba(212, 175, 55, 0.1), rgba(242, 169, 127, 0.08));
      color: var(--gold-dark, #9A7B2E);
      border: 1rpx solid rgba(212, 175, 55, 0.15);
      letter-spacing: 1rpx;
      white-space: nowrap;
    }
    .media-type-tag {
      font-size: 20rpx; color: #C2BBB2; font-weight: 600;
      white-space: nowrap;
    }
    .history-date {
      display: block; font-size: 22rpx; color: var(--text-muted, #A39B90); font-weight: 500;
      letter-spacing: 0.5rpx;
    }
  }

  .view-btn {
    flex-shrink: 0;
    width: 64rpx; height: 64rpx;
    border-radius: 50%;
    background: linear-gradient(135deg, #D4AF37, #F2A97F);
    display: flex; align-items: center; justify-content: center;
    margin-left: 16rpx;
    box-shadow: 0 6rpx 20rpx rgba(212, 175, 55, 0.2);
    transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);

    .view-arrow {
      font-size: 28rpx; color: #FFFFFF; font-weight: 800;
      line-height: 1;
    }

    &:active {
      transform: scale(0.88);
      box-shadow: 0 2rpx 8rpx rgba(212, 175, 55, 0.15);
    }
  }
}

/* ================= 高级沉浸式详情弹窗 ================= */
.detail-popup {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(250, 248, 245, 0.65); backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px);
  z-index: 1000; display: flex; align-items: center; justify-content: center; padding: 40rpx;
  animation: fadeInUp 0.4s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
}

.detail-content {
  width: 100%; max-height: 85vh; background: #FFFFFF; border-radius: 56rpx; padding: 48rpx 40rpx;
  box-shadow: 0 40rpx 100rpx rgba(212, 175, 55, 0.15), inset 0 2rpx 0 rgba(255,255,255,0.8);
  position: relative; overflow-y: auto; overflow-x: hidden;
}

/* 核心：沉浸式按压对比交互 */
.detail-interactive-compare {
  display: flex; flex-direction: column; align-items: center; margin-bottom: 40rpx;
}

.image-stack-container {
  width: 100%; height: 600rpx; position: relative; border-radius: 40rpx;
  overflow: hidden; background: #FDF8EF; box-shadow: 0 16rpx 40rpx rgba(0,0,0,0.06);
  border: 1rpx solid rgba(212, 175, 55, 0.1);
}

/* 绝对定位层叠，上层控制透明度 */
.img-layer {
  position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: block;
}
.img-original { z-index: 1; }
.img-repaired { z-index: 2; transition: opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
.fade-out { opacity: 0 !important; }

/* 状态徽章 */
.status-badge {
  position: absolute; top: 24rpx; left: 24rpx; z-index: 3;
  padding: 10rpx 24rpx; display: flex; align-items: center; gap: 12rpx;
  font-size: 24rpx; font-weight: 800; color: #5A4A32;
  .badge-dot { width: 12rpx; height: 12rpx; border-radius: 50%; background: var(--champagne-main); transition: background 0.3s; }
  .dot-original { background: #A39B90; }
}

/* 按压对比按钮 */
.compare-control {
  margin-top: -36rpx; z-index: 4; position: relative;
}
.compare-btn {
  display: inline-flex; align-items: center; background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(16px); padding: 12rpx 32rpx 12rpx 12rpx; border-radius: 64rpx;
  box-shadow: 0 12rpx 32rpx rgba(212, 175, 55, 0.15); border: 1rpx solid rgba(255, 255, 255, 0.9);
  user-select: none; /* 防止误触文字选择 */
  .compare-icon-wrap { width: 64rpx; height: 64rpx; border-radius: 50%; background: linear-gradient(135deg, var(--gold-main), var(--champagne-main)); display: flex; align-items: center; justify-content: center; margin-right: 16rpx; }
  .c-icon { font-size: 32rpx; color: #FFF; }
  .compare-text { font-size: 26rpx; font-weight: 800; color: #5A4A32; }
}

/* 音视频模块样式优化 */
.detail-audio { margin-bottom: 40rpx; }
.audio-player-card {
  display: flex; align-items: center; background: #FDFBF8; border-radius: 32rpx; padding: 32rpx;
  border: 1rpx solid rgba(212, 175, 55, 0.2);
  .audio-icon-wrap { width: 96rpx; height: 96rpx; border-radius: 50%; background: #FFF; display: flex; align-items: center; justify-content: center; box-shadow: 0 8rpx 24rpx rgba(0,0,0,0.05); margin-right: 24rpx; transition: all 0.3s; }
  .is-playing { box-shadow: 0 0 0 8rpx rgba(212, 175, 55, 0.1); transform: scale(1.05); }
  .audio-icon { font-size: 40rpx; }
  .audio-info { flex: 1; }
  .audio-title { display: block; font-size: 32rpx; font-weight: 800; color: #5A4A32; margin-bottom: 8rpx; }
  .audio-status { display: block; font-size: 24rpx; color: var(--gold-dark); font-weight: 600; }
}
.video-player { width: 100%; height: 400rpx; border-radius: 32rpx; margin-bottom: 40rpx; box-shadow: 0 16rpx 40rpx rgba(0,0,0,0.06); }

/* 详情信息 */
.detail-info {
  padding: 32rpx; margin-bottom: 40rpx;
  .detail-row {
    display: flex; justify-content: space-between; padding: 16rpx 0; border-bottom: 1px dashed rgba(212, 175, 55, 0.2);
    &:last-child { border-bottom: none; padding-bottom: 0; }
    .detail-label { font-size: 26rpx; color: #A39B90; font-weight: 600; }
    .detail-value { font-size: 26rpx; color: #3D352B; font-weight: 800; }
    .gold-text { color: var(--gold-dark); }
  }
}

/* 操作与关闭按钮 */
.detail-actions {
  display: flex; gap: 24rpx;
  .detail-btn {
    flex: 1; padding: 28rpx 0; text-align: center; border-radius: 32rpx; font-size: 30rpx; font-weight: 800;
    &.download-btn { background: linear-gradient(135deg, var(--gold-main), var(--champagne-main)); color: #FFF; box-shadow: 0 12rpx 32rpx rgba(212, 175, 55, 0.25); }
    &.repair-btn { background: linear-gradient(135deg, #667EEA, #764BA2); color: #FFF; box-shadow: 0 12rpx 32rpx rgba(118, 75, 162, 0.25); }
    &.delete-detail-btn { background: #FFFFFF; color: #FF7676; border: 2rpx solid #FF7676; }
  }
}

.close-btn {
  position: absolute; top: 32rpx; right: 32rpx; width: 72rpx; height: 72rpx;
  display: flex; align-items: center; justify-content: center;
  background: rgba(255,255,255,0.9); border-radius: 50%; font-size: 32rpx; color: #A39B90;
  box-shadow: 0 8rpx 24rpx rgba(0,0,0,0.05); z-index: 10;
}

/* 空状态等辅助样式... */
.empty-state {
  display: flex; flex-direction: column; align-items: center; padding: 160rpx 0;
  .empty-glass-icon { width: 160rpx; height: 160rpx; border-radius: 50%; background: rgba(255, 255, 255, 0.6); backdrop-filter: blur(20px); display: flex; align-items: center; justify-content: center; margin-bottom: 32rpx; border: 1px solid rgba(255, 255, 255, 0.9); box-shadow: 0 16rpx 40rpx rgba(0,0,0,0.03); }
  .empty-emoji { font-size: 80rpx; filter: drop-shadow(0 8rpx 16rpx rgba(0,0,0,0.1)); }
  .empty-text { font-size: 32rpx; font-weight: 800; color: #5A4A32; margin-bottom: 12rpx; }
  .empty-hint { font-size: 24rpx; color: #A39B90; font-weight: 500; }
}
.load-more { text-align: center; padding: 40rpx 0; .load-more-text { font-size: 26rpx; color: var(--gold-dark); font-weight: 800; letter-spacing: 2rpx; } }

/* ================= 自定义确认删除弹窗 ================= */
.confirm-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(30, 25, 18, 0.55);
  backdrop-filter: blur(8rpx);
  z-index: 9999;
  display: flex; align-items: center; justify-content: center;
  padding: 60rpx;
}
.confirm-dialog {
  width: 100%; max-width: 560rpx;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(24rpx);
  border-radius: 40rpx;
  padding: 48rpx 40rpx 36rpx;
  text-align: center;
  box-shadow: 0 24rpx 64rpx rgba(0, 0, 0, 0.18);
  border: 1rpx solid rgba(255, 255, 255, 0.9);
}
.confirm-icon-wrap {
  width: 88rpx; height: 88rpx; border-radius: 50%;
  background: linear-gradient(135deg, #FEF3E0, #FDE8C8);
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 24rpx;
}
.confirm-icon { font-size: 44rpx; }
.confirm-title {
  display: block; font-size: 34rpx; font-weight: 800; color: #3D352B;
  margin-bottom: 16rpx;
}
.confirm-content {
  display: block; font-size: 28rpx; color: #7A6F62; line-height: 1.6;
  margin-bottom: 36rpx;
}
.confirm-actions { display: flex; gap: 24rpx; }
.confirm-btn {
  flex: 1; padding: 22rpx 0; border-radius: 56rpx;
  font-size: 30rpx; font-weight: 800; text-align: center;
}
.confirm-cancel {
  background: #F3F2F0; color: #8C7A5A;
  &:active { background: #E8E4DD; }
}
.confirm-ok {
  background: linear-gradient(135deg, #FF7676, #E53E3E); color: #FFF;
  box-shadow: 0 8rpx 24rpx rgba(229, 62, 62, 0.25);
  &:active { opacity: 0.85; }
}
</style>
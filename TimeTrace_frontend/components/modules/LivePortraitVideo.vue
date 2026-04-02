<template>
  <div class="liveportrait-video-container relative w-full h-full flex flex-col items-center justify-center p-8">
    <!-- 动态背景装饰 -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="absolute -top-20 -right-20 w-40 h-40 bg-indigo-200/20 rounded-full blur-3xl animate-pulse-slow"></div>
      <div class="absolute -bottom-20 -left-20 w-40 h-40 bg-purple-200/20 rounded-full blur-3xl animate-pulse-slow delay-1000"></div>
      <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-80 h-80 bg-gradient-to-r from-indigo-100/10 to-purple-100/10 rounded-full blur-2xl"></div>
    </div>

    <!-- 处理中状态 -->
    <div v-if="isProcessing" class="text-center z-10">
      <!-- 动态加载动画 -->
      <div class="relative mb-8">
        <div class="w-32 h-32 mx-auto relative">
          <!-- 外圈旋转动画 -->
          <div class="absolute inset-0 border-4 border-indigo-200/30 rounded-full"></div>
          <div class="absolute inset-2 border-4 border-indigo-500 rounded-full border-t-transparent animate-spin"></div>
          
          <!-- 内圈脉冲动画 -->
          <div class="absolute inset-6 border-4 border-purple-400/50 rounded-full animate-ping"></div>
          
          <!-- 中心图标 -->
          <div class="absolute inset-8 bg-gradient-to-br from-indigo-100 to-white rounded-full flex items-center justify-center shadow-lg">
            <FontAwesomeIcon icon="fa-solid fa-video" class="text-2xl text-indigo-600" />
          </div>
        </div>
        
        <!-- 浮动粒子 -->
        <div class="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-4">
          <div class="w-3 h-3 bg-indigo-400 rounded-full animate-bounce"></div>
        </div>
      </div>
      
      <!-- 进度信息 -->
      <div class="space-y-4">
        <h3 class="text-2xl font-bold text-gray-800 tracking-wide">正在让人像开口说话...</h3>
        <p class="text-lg text-indigo-600 font-medium">{{ loadingMsg }}</p>
        
        <!-- 进度条 -->
        <div class="w-80 mx-auto">
          <div class="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div 
              class="h-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-300"
              :style="{ width: progress + '%' }"
            ></div>
          </div>
          <div class="flex justify-between text-sm text-gray-500 mt-2">
            <span>0%</span>
            <span>{{ Math.round(progress) }}%</span>
            <span>100%</span>
          </div>
        </div>
        
        <!-- 提示信息 -->
        <div class="text-sm text-gray-400 space-y-1">
          <p>🤖 AI正在分析视频动作特征...</p>
          <p>🎭 迁移面部表情动画...</p>
          <p>🎵 合成音频与视频...</p>
          <p>🎬 生成最终说话视频...</p>
        </div>
      </div>
    </div>

    <!-- 完成状态 -->
    <div v-else-if="videoUrl" class="text-center z-10 w-full max-w-4xl">
      <!-- 视频播放器 -->
          <div class="relative group">
            <!-- 视频容器 -->
            <div class="relative aspect-video bg-black rounded-2xl overflow-hidden shadow-2xl transform transition-transform duration-300 group-hover:scale-[1.02]">
              <video 
                :src="videoUrl" 
                controls 
                preload="metadata"
                autoplay
                muted
                playsinline
                loop
                crossorigin="anonymous"
                class="w-full h-full object-contain"
                @loadedmetadata="onVideoLoaded"
                @play="onVideoPlay"
                @pause="onVideoPause"
                @error="onVideoError"
                @canplay="onVideoCanPlay"
                @waiting="onVideoWaiting"
                @stalled="onVideoStalled"
              >
                您的浏览器不支持视频播放，请使用现代浏览器如Chrome、Firefox或Edge
                <track kind="captions" src="" srclang="zh" label="中文">
              </video>
              
              <!-- 播放状态指示器 - 完全修复点击无效问题 -->
              <div v-if="!isPlaying" class="absolute inset-0 flex items-center justify-center bg-black/30 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
                <div class="w-20 h-20 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center cursor-pointer pointer-events-auto" @click="triggerVideoPlay" @mousedown.stop @touchstart.stop>
                  <FontAwesomeIcon icon="fa-solid fa-play" class="text-3xl text-white" />
                </div>
              </div>
            </div>
        
        <!-- 视频信息 -->
        <div class="mt-6 text-center">
          <h3 class="text-2xl font-bold text-gray-800 mb-2">🎉 人像复活完成！</h3>
          <p class="text-gray-600 mb-4">照片已经根据音频内容开口说话</p>
          
          <!-- 视频信息卡片 -->
          <div class="inline-flex items-center gap-4 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl p-4 mb-6">
            <div class="flex items-center gap-2">
              <FontAwesomeIcon icon="fa-solid fa-clock" class="text-indigo-500" />
              <span class="text-sm font-medium text-gray-700">{{ videoDuration || '加载中...' }}</span>
            </div>
            <div class="w-px h-6 bg-gray-300"></div>
            <div class="flex items-center gap-2">
              <FontAwesomeIcon icon="fa-solid fa-video" class="text-purple-500" />
              <span class="text-sm font-medium text-gray-700">视频驱动</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 操作按钮 - 添加返回和重新生成按钮 -->
      <div class="flex gap-4 justify-center mt-8">
        <button 
          @click="onBack" 
          class="px-8 py-3 rounded-xl bg-gradient-to-r from-gray-100 to-gray-200 hover:from-gray-200 hover:to-gray-300 text-gray-700 transition-all transform hover:-translate-y-0.5 font-bold flex items-center gap-2 text-sm shadow-lg"
        >
          <FontAwesomeIcon icon="fa-solid fa-arrow-left" /> 返回
        </button>
        <button 
          @click="onRegenerate" 
          class="px-8 py-3 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600 text-white transition-all transform hover:-translate-y-0.5 font-bold flex items-center gap-2 text-sm shadow-lg"
        >
          <FontAwesomeIcon icon="fa-solid fa-rotate" /> 重新生成
        </button>
      </div>
    </div>

    <!-- 初始状态 -->
    <div v-else class="text-center z-10 opacity-60">
      <div class="w-64 h-64 mx-auto mb-6 bg-gradient-to-tr from-indigo-100/50 to-purple-100/50 rounded-full flex items-center justify-center shadow-inner border border-indigo-100">
        <FontAwesomeIcon icon="fa-solid fa-video" class="text-8xl text-indigo-200" />
      </div>
      <h2 class="text-2xl font-serif text-gray-800 mb-2">灵动·人像复活</h2>
      <p class="text-base text-gray-400">上传照片、驱动视频和音频，让静态照片开口说话</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'

interface Props {
  isProcessing: boolean
  loadingMsg: string
  videoUrl: string | null
  progress: number
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'regenerate'): void
  (e: 'back'): void
}>()

// 视频状态
const isPlaying = ref(false)
const videoDuration = ref('')

// 视频事件处理
const onVideoLoaded = (event: Event) => {
  const video = event.target as HTMLVideoElement
  const duration = Math.floor(video.duration)
  const minutes = Math.floor(duration / 60)
  const seconds = duration % 60
  videoDuration.value = `${minutes}:${seconds.toString().padStart(2, '0')}`
}

const onVideoPlay = () => {
  isPlaying.value = true
}

const onVideoPause = () => {
  isPlaying.value = false
}

// 视频错误处理
const onVideoError = (event: Event) => {
  const video = event.target as HTMLVideoElement
  console.error('视频播放错误:', video.error)
  
  // 尝试重新加载视频
  if (props.videoUrl) {
    video.load()
  }
}

// 视频可以播放
const onVideoCanPlay = (event: Event) => {
  console.log('视频可以播放了')
  const video = event.target as HTMLVideoElement
  video.play().catch(e => {
    console.warn('自动播放失败:', e)
    // 自动播放失败时，显示播放按钮让用户手动点击
  })
}

// 视频等待加载
const onVideoWaiting = (event: Event) => {
  console.log('视频正在等待加载数据...')
}

// 视频加载停滞
const onVideoStalled = (event: Event) => {
  console.warn('视频加载停滞，尝试重新加载...')
  const video = event.target as HTMLVideoElement
  if (props.videoUrl) {
    video.load()
  }
}

// 触发视频播放 - 悬浮播放按钮点击事件
const triggerVideoPlay = () => {
  const videoElement = document.querySelector('video') as HTMLVideoElement
  if (videoElement) {
    videoElement.play().catch(e => {
      console.warn('悬浮播放按钮点击失败:', e)
      // 如果自动播放失败，显示原生播放控件让用户手动点击
      videoElement.controls = true
    })
  }
}

// 返回
const onBack = () => {
  emit('back')
}

// 重新生成
const onRegenerate = () => {
  emit('regenerate')
}

// 清理资源
onUnmounted(() => {
  if (props.videoUrl && props.videoUrl.startsWith('blob:')) {
    URL.revokeObjectURL(props.videoUrl)
  }
})
</script>

<style scoped>
.liveportrait-video-container {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
}

.animate-pulse-slow {
  animation: pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.delay-1000 {
  animation-delay: 1s;
}
</style>
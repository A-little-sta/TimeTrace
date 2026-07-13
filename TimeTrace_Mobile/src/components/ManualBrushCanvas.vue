<template>
  <!-- 拂尘手动修复 Canvas 涂抹组件 —— 参照 Web 前端 BrushCanvas.vue 实现 -->
  <view class="manual-brush-wrap" @touchmove.stop.prevent>
    <view class="canvas-zoom-indicator" v-if="canvasScale !== 1">{{ Math.round(canvasScale * 100) }}%</view>
    
    <!-- 可绘制区域：图片 + Canvas 叠加 -->
    <view class="canvas-draw-area">
      <image class="canvas-bg-image" :src="imageUrl" mode="aspectFit" />
      <canvas 
        canvas-id="manualRepairCanvas" 
        id="manualRepairCanvas" 
        class="repair-canvas" 
        :style="{ width: canvasWidth + 'px', height: canvasHeight + 'px' }" 
        disable-scroll
      ></canvas>
      <!-- 透明触摸拦截层：确保触摸事件不被 image 吞掉 -->
      <view class="canvas-touch-cover" 
        @touchstart.stop.prevent="onTouchStart"
        @touchmove.stop.prevent="onTouchMove"
        @touchend.stop.prevent="onTouchEnd"
        @touchcancel.stop.prevent="onTouchEnd"
      ></view>
    </view>
    
    <!-- 工具栏 -->
    <view class="canvas-toolbar">
      <text class="canvas-hint">涂抹需要修复的区域 · {{ brushMode === 'draw' ? '画笔' : '橡皮' }}模式</text>
      <view class="paint-tool-row">
        <view class="paint-tool-btn paint-mode-btn" @tap="toggleBrushMode">
          <text>{{ brushMode === 'draw' ? '画笔' : '橡皮' }}</text>
        </view>
        <view class="paint-tool-btn paint-clear-btn" @tap="clearCanvas">
          <text>清空涂抹</text>
        </view>
      </view>
      <view class="brush-size-control">
        <text class="brush-label">笔刷大小</text>
        <text class="brush-size-value">{{ brushSize }}px</text>
        <slider 
          :value="brushSize" :min="5" :max="60" :step="1" 
          activeColor="#D4AF37" backgroundColor="#E8DCC8" block-size="16" 
          @change="brushSize = $event.detail.value" 
          style="flex: 1; margin: 0 16rpx;" 
        />
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'

const props = defineProps<{
  imageUrl: string
}>()

const emit = defineEmits<{
  'has-strokes': [value: boolean]
  'mask-export': [tempPath: string]
}>()

const canvasWidth = ref(0)
const canvasHeight = ref(0)
const brushSize = ref(20)
const brushMode = ref<'draw' | 'erase'>('draw')
const canvasScale = ref(1)
const isPainting = ref(false)
const hasStrokes = ref(false)

let canvasRect = { left: 0, top: 0, width: 0, height: 0 }
let lastX = 0
let lastY = 0
let strokePaths: Array<{ points: Array<{ x: number; y: number }>; mode: 'draw' | 'erase'; size: number }> = []

// 双指缩放
let lastPinchDistance = 0
let isPinching = false

// ========== Canvas 初始化 ==========
const initCanvas = () => {
  const query = uni.createSelectorQuery()
  query.select('.canvas-draw-area').boundingClientRect((rect: any) => {
    if (!rect) {
      // 重试
      setTimeout(() => initCanvas(), 100)
      return
    }
    canvasRect = { left: rect.left, top: rect.top, width: rect.width, height: rect.height }
    canvasWidth.value = rect.width
    canvasHeight.value = rect.height
    
    nextTick(() => {
      initCanvasInternal()
    })
  }).exec()
}

const initCanvasInternal = () => {
  const ctx = uni.createCanvasContext('manualRepairCanvas')
  ctx.fillStyle = 'rgba(255,107,53,0.85)'
  ctx.fillStyle = 'rgba(0,0,0,0)'
  ctx.clearRect(0, 0, canvasWidth.value, canvasHeight.value)
  ctx.draw()
}

// ========== 触摸事件 ==========
const onTouchStart = (e: any) => {
  // 每次触摸开始时刷新画布位置，防止页面滚动后坐标偏移
  const query = uni.createSelectorQuery()
  query.select('.canvas-draw-area').boundingClientRect((rect: any) => {
    if (rect) {
      canvasRect = { left: rect.left, top: rect.top, width: rect.width, height: rect.height }
    }
  }).exec()

  // 双指缩放
  if (e.touches.length === 2) {
    isPinching = true
    lastPinchDistance = getDistance(e.touches[0], e.touches[1])
    return
  }

  isPainting.value = true
  const touch = e.touches[0]
  const x = touch.clientX - canvasRect.left
  const y = touch.clientY - canvasRect.top
  lastX = x
  lastY = y

  // 开始新的笔触路径
  strokePaths.push({ points: [{ x, y }], mode: brushMode.value, size: brushSize.value })
  drawDot(x, y)
}

const onTouchMove = (e: any) => {
  // 双指缩放
  if (e.touches.length === 2 && isPinching) {
    const newDist = getDistance(e.touches[0], e.touches[1])
    if (lastPinchDistance > 0) {
      const scaleChange = newDist / lastPinchDistance
      canvasScale.value = Math.max(1, Math.min(5, canvasScale.value * scaleChange))
    }
    lastPinchDistance = newDist
    return
  }

  if (!isPainting.value) return
  
  const touch = e.touches[0]
  const x = touch.clientX - canvasRect.left
  const y = touch.clientY - canvasRect.top

  drawLine(lastX, lastY, x, y)

  // 记录到当前笔触
  const currentStroke = strokePaths[strokePaths.length - 1]
  if (currentStroke) {
    currentStroke.points.push({ x, y })
  }

  hasStrokes.value = true
  emit('has-strokes', true)
  lastX = x
  lastY = y
}

const onTouchEnd = () => {
  isPainting.value = false
  isPinching = false
  lastPinchDistance = 0
}

// ========== 绘制 ==========
const drawDot = (x: number, y: number) => {
  const ctx = uni.createCanvasContext('manualRepairCanvas')
  ctx.beginPath()
  if (brushMode.value === 'draw') {
    ctx.fillStyle = 'rgba(255,107,53,0.85)'
  } else {
    ctx.fillStyle = 'rgba(255,255,255,0.5)'
  }
  ctx.arc(x, y, brushSize.value / 2, 0, 2 * Math.PI)
  ctx.fill()
  ctx.draw(true)
}

const drawLine = (fromX: number, fromY: number, toX: number, toY: number) => {
  const ctx = uni.createCanvasContext('manualRepairCanvas')
  ctx.beginPath()
  if (brushMode.value === 'draw') {
    ctx.strokeStyle = 'rgba(255,107,53,0.85)'
  } else {
    ctx.strokeStyle = 'rgba(255,255,255,0.5)'
  }
  ctx.lineWidth = brushSize.value
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'
  ctx.moveTo(fromX, fromY)
  ctx.lineTo(toX, toY)
  ctx.stroke()
  ctx.draw(true)
}

const getDistance = (t1: any, t2: any): number => {
  const dx = t1.clientX - t2.clientX
  const dy = t1.clientY - t2.clientY
  return Math.sqrt(dx * dx + dy * dy)
}

// ========== 工具方法 ==========
const toggleBrushMode = () => {
  brushMode.value = brushMode.value === 'draw' ? 'erase' : 'draw'
}

const clearCanvas = () => {
  const ctx = uni.createCanvasContext('manualRepairCanvas')
  ctx.clearRect(0, 0, canvasWidth.value, canvasHeight.value)
  ctx.draw()
  strokePaths = []
  hasStrokes.value = false
  emit('has-strokes', false)
}

// ========== 导出遮罩基岩 (mask) ==========
const exportMask = (): Promise<string> => {
  return new Promise((resolve, reject) => {
    uni.canvasToTempFilePath({
      canvasId: 'manualRepairCanvas',
      destWidth: canvasWidth.value,
      destHeight: canvasHeight.value,
      success: (res) => resolve(res.tempFilePath),
      fail: (err) => reject(err)
    })
  })
}

// 暴露方法给父组件
defineExpose({
  exportMask,
  hasStrokes,
  clearCanvas,
  initCanvas
})

// 监听图片 URL 变化，自动初始化
watch(() => props.imageUrl, (newUrl) => {
  if (newUrl) {
    nextTick(() => {
      setTimeout(() => initCanvas(), 100)
    })
  }
})

onMounted(() => {
  if (props.imageUrl) {
    setTimeout(() => initCanvas(), 150)
  }
})
</script>

<style lang="scss" scoped>
.manual-brush-wrap { width: 100%; }

.canvas-zoom-indicator {
  position: absolute; top: 16rpx; right: 16rpx; z-index: 20;
  background: rgba(0,0,0,0.5); color: #fff; padding: 4rpx 16rpx;
  border-radius: 20rpx; font-size: 22rpx;
}

.canvas-draw-area { 
  width: 100%; height: 650rpx; position: relative; overflow: hidden; background: #F5F0E8;
}
.canvas-bg-image { width: 100%; height: 100%; display: block; position: absolute; top: 0; left: 0; z-index: 1; pointer-events: none; }
.repair-canvas { position: absolute; top: 0; left: 0; z-index: 5; touch-action: none; }
.canvas-touch-cover { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 10; }

.canvas-toolbar {
  flex-shrink: 0; padding: 16rpx 24rpx;
  background: rgba(245, 240, 232, 0.95);
  border-top: 1rpx solid rgba(212, 175, 55, 0.15);
}
.canvas-hint { font-size: 24rpx; color: #8B7355; display: block; text-align: center; margin-bottom: 12rpx; }

.paint-tool-row { display: flex; gap: 16rpx; margin-bottom: 16rpx; }
.paint-tool-btn {
  flex: 1; height: 72rpx; display: flex; align-items: center; justify-content: center;
  border-radius: 36rpx; font-size: 26rpx; font-weight: 600;
  transition: all 0.2s;
  &:active { transform: scale(0.95); }
}
.paint-mode-btn { background: linear-gradient(135deg, rgba(212, 175, 55, 0.15), rgba(212, 175, 55, 0.05)); border: 1rpx solid rgba(212, 175, 55, 0.3); color: #5C4A2E; }
.paint-clear-btn { background: rgba(0,0,0,0.05); border: 1rpx solid rgba(0,0,0,0.1); color: #8B7355; }

.brush-size-control {
  display: flex; align-items: center; padding: 0 8rpx;
}
.brush-label { font-size: 24rpx; color: #8B7355; width: 120rpx; }
.brush-size-value { font-size: 24rpx; color: #5C4A2E; font-weight: 600; width: 60rpx; text-align: center; }
</style>
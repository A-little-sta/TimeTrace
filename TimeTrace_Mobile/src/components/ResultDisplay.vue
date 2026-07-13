<template>
  <!-- 修复结果展示 —— 通用组件，所有模块共用 -->
  <view class="result-display">
    
    <!-- 处理中进度展示 -->
    <view v-if="isProcessing" class="processing-overlay">
      <view class="scanner-line"></view>
      <view class="progress-capsule glass-panel-light">
        <text class="loading-text">{{ loadingMsg }}</text>
        <view class="progress-track">
          <view class="progress-fill" :style="{ width: progress + '%' }"></view>
        </view>
        <text class="progress-num">{{ progress }}%</text>
      </view>
    </view>

    <!-- 修复结果图片展示 -->
    <view v-if="!isProcessing && (resultUrl || imageUrl)" class="result-image-area">
      <view class="single-image-wrap">
        <image 
          class="main-image" 
          :src="isHoldingCompare ? imageUrl : (resultUrl || imageUrl)" 
          mode="aspectFit" 
          @error="onImageError"
        />
        <view class="status-badge glass-panel-light">
          <text class="badge-dot" :class="{ 'dot-original': !resultUrl || isHoldingCompare }"></text>
          <text>{{ isHoldingCompare ? '原图' : (!resultUrl ? '原图就绪' : '修复后') }}</text>
        </view>
      </view>

      <!-- 长按对比按钮（独立于图片盒子外） -->
      <view v-if="resultUrl" class="compare-bar">
        <view 
          class="compare-btn float-hover" 
          @touchstart.prevent="emit('hold-start')"
          @touchend.prevent="emit('hold-end')"
          @touchcancel.prevent="emit('hold-end')"
        >
          <text class="compare-icon">👆</text>
          <text class="compare-text">{{ isHoldingCompare ? '松手查看修复效果' : '长按查看原图' }}</text>
        </view>
      </view>

      <!-- 操作按钮 -->
      <view v-if="resultUrl" class="result-actions-row">
        <view class="ra-btn float-hover" @tap="emit('download')">
          <text class="ra-icon">⬇</text><text class="ra-label">保存</text>
        </view>
        <view class="ra-btn float-hover" @tap="emit('continue')">
          <text class="ra-icon">↻</text><text class="ra-label">继续修复</text>
        </view>
        <view class="ra-btn float-hover" @tap="emit('reset')">
          <text class="ra-icon">✕</text><text class="ra-label">重新开始</text>
        </view>
      </view>
    </view>

  </view>
</template>

<script setup lang="ts">
defineProps<{
  imageUrl: string
  resultUrl: string
  isProcessing: boolean
  loadingMsg: string
  progress: number
  isHoldingCompare: boolean
}>()

const emit = defineEmits<{
  'hold-start': []
  'hold-end': []
  'download': []
  'continue': []
  'reset': []
}>()

const onImageError = (e: any) => {
  console.warn('结果图片加载失败:', e)
}
</script>

<style lang="scss" scoped>
.result-display { width: 100%; }

.single-image-wrap {
  width: 100%; height: 650rpx; position: relative; display: flex;
  align-items: center; justify-content: center;
}
.main-image { width: 100%; height: 100%; display: block; }

.status-badge {
  position: absolute; top: 20rpx; right: 20rpx; z-index: 5;
  display: flex; align-items: center; gap: 8rpx; padding: 8rpx 20rpx;
  border-radius: 40rpx; flex-direction: row;
}
.badge-dot { width: 12rpx; height: 12rpx; border-radius: 50%; background: #D4AF37; }
.dot-original { background: #A0A0A0; }

/* 进度条 */
.processing-overlay { position: relative; width: 100%; }
.scanner-line {
  width: 100%; height: 4rpx; background: linear-gradient(90deg, transparent, #D4AF37, transparent);
  animation: scanSweep 2s ease-in-out infinite;
}
@keyframes scanSweep {
  0% { opacity: 0.3; transform: scaleX(0.5); }
  50% { opacity: 1; transform: scaleX(1); }
  100% { opacity: 0.3; transform: scaleX(0.5); }
}
.progress-capsule {
  margin: 24rpx; padding: 24rpx 32rpx; border-radius: 24rpx;
  display: flex; flex-direction: column; gap: 12rpx;
}
.loading-text { font-size: 28rpx; color: #5C4A2E; text-align: center; }
.progress-track { width: 100%; height: 12rpx; background: #E8DCC8; border-radius: 6rpx; overflow: hidden; }
.progress-fill { height: 100%; background: linear-gradient(90deg, #D4AF37, #C9A02B); border-radius: 6rpx; transition: width 0.3s; }
.progress-num { font-size: 24rpx; color: #8B7355; text-align: center; }

/* 对比按钮（独立于图片区域外） */
.compare-bar {
  display: flex; justify-content: center;
  padding: 20rpx 0; margin-top: 8rpx;
}
.compare-btn {
  display: flex; align-items: center; gap: 10rpx;
  padding: 16rpx 40rpx; 
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.15), rgba(212, 175, 55, 0.05));
  border: 2rpx solid rgba(212, 175, 55, 0.3);
  border-radius: 48rpx;
  &:active { background: rgba(212, 175, 55, 0.3); transform: scale(0.96); }
}
.compare-icon { font-size: 32rpx; }
.compare-text { font-size: 26rpx; color: #5C4A2E; }

/* 操作按钮 */
.result-actions-row {
  display: flex; gap: 16rpx; padding: 16rpx 0; justify-content: center;
}
.ra-btn {
  display: flex; align-items: center; gap: 6rpx;
  padding: 16rpx 28rpx; border-radius: 40rpx;
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.12), rgba(212, 175, 55, 0.04));
  border: 1rpx solid rgba(212, 175, 55, 0.25);
  &:active { background: rgba(212, 175, 55, 0.25); transform: scale(0.95); }
}
.ra-icon { font-size: 26rpx; }
.ra-label { font-size: 26rpx; color: #5C4A2E; }
</style>
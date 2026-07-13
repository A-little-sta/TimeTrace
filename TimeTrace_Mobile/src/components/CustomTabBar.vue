<template>
  <view class="custom-tabbar-wrapper">
    <view class="custom-tabbar">
      <view
        v-for="(item, index) in tabList"
        :key="index"
        class="tabbar-item"
        :class="{ active: selectedIndex === index }"
        @tap="switchTab(index)"
      >
        <view class="tab-icon-indicator">
          <view v-if="index === 0" class="icon-wrench">
            <view class="wrench-handle"></view>
            <view class="wrench-head"></view>
          </view>
          <view v-else-if="index === 1" class="icon-gallery">
            <view class="gallery-frame"></view>
            <view class="gallery-mountain"></view>
            <view class="gallery-sun"></view>
          </view>
          <view v-else-if="index === 2" class="icon-clock">
            <view class="clock-face"></view>
            <view class="clock-hand-short"></view>
            <view class="clock-hand-long"></view>
          </view>
          <view v-else class="icon-help">
            <view class="help-circle"></view>
            <text class="help-question">?</text>
          </view>
        </view>
        <text class="tab-text">{{ item.text }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  selected: number
}>()

const selectedIndex = computed(() => props.selected)

const tabList = [
  { text: '修复工坊', pagePath: '/pages/workshop/workshop' },
  { text: '时光图库', pagePath: '/pages/gallery/gallery' },
  { text: '创作时光轴', pagePath: '/pages/history/history' },
  { text: '使用指南', pagePath: '/pages/help/help' }
]

const switchTab = (index: number) => {
  if (selectedIndex.value === index) return
  uni.switchTab({ url: tabList[index].pagePath })
}
</script>

<style lang="scss" scoped>
/* 外层包裹器，处理底部安全距离 */
.custom-tabbar-wrapper {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding-bottom: calc(30rpx + env(safe-area-inset-bottom));
  z-index: 999;
  pointer-events: none; /* 让事件穿透包裹层，只在tabbar上生效 */
}

/* 悬浮毛玻璃 TabBar */
.custom-tabbar {
  pointer-events: auto;
  margin: 0 40rpx; /* 左右留白，形成悬浮感 */
  height: 128rpx;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px); /* 核心：毛玻璃效果 */
  -webkit-backdrop-filter: blur(20px);
  border-radius: 64rpx; /* 大圆角 */
  display: flex;
  align-items: center;
  justify-content: space-around;
  box-shadow: 0 16rpx 40rpx rgba(212, 175, 55, 0.12); /* 流光金色的弥散阴影 */
  border: 1rpx solid rgba(255, 255, 255, 0.5); /* 边缘高光，增加玻璃质感 */
}

.tabbar-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  height: 100%;
  position: relative;
  
  .tab-text {
    font-size: 20rpx;
    color: var(--text-muted);
    margin-top: 6rpx;
    font-weight: 500;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  &.active .tab-text {
    color: var(--gold-main); /* 选中后文字变金 */
    font-weight: 700;
  }
}

/* MD3 风格的胶囊指示器 */
.tab-icon-indicator {
  width: 96rpx;
  height: 56rpx;
  border-radius: 28rpx; /* 胶囊形状 */
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  background: transparent;
}

.active .tab-icon-indicator {
  /* 选中时的背景：香槟橙到流光金的柔和渐变 */
  background: linear-gradient(135deg, rgba(252, 232, 213, 0.8), rgba(245, 228, 195, 0.8));
  transform: scale(1.05); /* 点击时微微放大 */
}

/* ================= 纯CSS图标重构优化 ================= */
/* 统一图标大小和默认颜色 */
.icon-wrench, .icon-gallery, .icon-clock, .icon-help {
  position: relative;
  width: 36rpx;
  height: 36rpx;
}

/* 1. 修复工坊 - 扳手 */
.icon-wrench {
  .wrench-handle {
    width: 6rpx;
    height: 22rpx;
    background: var(--text-muted);
    border-radius: 4rpx;
    position: absolute;
    bottom: 2rpx;
    left: 50%;
    transform: translateX(-50%) rotate(-45deg);
    transform-origin: bottom center;
    transition: all 0.3s;
  }
  .wrench-head {
    width: 16rpx;
    height: 16rpx;
    border: 4rpx solid var(--text-muted);
    border-radius: 50%;
    position: absolute;
    top: 2rpx;
    left: 50%;
    transform: translateX(-50%);
    transition: all 0.3s;
  }
}
.active .icon-wrench {
  .wrench-handle { background: var(--champagne-main); }
  .wrench-head { border-color: var(--gold-main); }
}

/* 2. 时光图库 - 风景 */
.icon-gallery {
  .gallery-frame {
    width: 34rpx;
    height: 26rpx;
    border: 3.5rpx solid var(--text-muted);
    border-radius: 6rpx;
    position: absolute;
    bottom: 2rpx;
    left: 1rpx;
    transition: all 0.3s;
  }
  .gallery-mountain {
    width: 0;
    height: 0;
    border-left: 9rpx solid transparent;
    border-right: 9rpx solid transparent;
    border-bottom: 11rpx solid var(--text-muted);
    position: absolute;
    bottom: 5rpx;
    left: 5rpx;
    transition: all 0.3s;
  }
  .gallery-sun {
    width: 7rpx;
    height: 7rpx;
    background: var(--text-muted);
    border-radius: 50%;
    position: absolute;
    top: 6rpx;
    right: 7rpx;
    transition: all 0.3s;
  }
}
.active .icon-gallery {
  .gallery-frame { border-color: var(--gold-main); }
  .gallery-mountain { border-bottom-color: var(--champagne-main); }
  .gallery-sun { background: var(--champagne-main); }
}

/* 3. 创作时光轴 - 时钟 */
.icon-clock {
  .clock-face {
    width: 30rpx;
    height: 30rpx;
    border: 3.5rpx solid var(--text-muted);
    border-radius: 50%;
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    transition: all 0.3s;
  }
  .clock-hand-short {
    width: 3.5rpx;
    height: 9rpx;
    background: var(--text-muted);
    border-radius: 2rpx;
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -100%) rotate(-30deg);
    transform-origin: bottom center;
    transition: all 0.3s;
  }
  .clock-hand-long {
    width: 3.5rpx;
    height: 13rpx;
    background: var(--text-muted);
    border-radius: 2rpx;
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -100%) rotate(60deg);
    transform-origin: bottom center;
    transition: all 0.3s;
  }
}
.active .icon-clock {
  .clock-face { border-color: var(--gold-main); }
  .clock-hand-short, .clock-hand-long { background: var(--champagne-main); }
}

/* 4. 使用指南 - 问号 */
.icon-help {
  .help-circle {
    width: 30rpx;
    height: 30rpx;
    border: 3.5rpx solid var(--text-muted);
    border-radius: 50%;
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    transition: all 0.3s;
  }
  .help-question {
    font-size: 20rpx;
    font-weight: 800;
    color: var(--text-muted);
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    transition: all 0.3s;
  }
}
.active .icon-help {
  .help-circle { border-color: var(--gold-main); }
  .help-question { color: var(--champagne-main); }
}
</style>
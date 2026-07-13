<template>
  <view class="help-page">
    <view class="page-header animate-fade-in-up" style="animation-delay: 0s;">
      <text class="page-title">使用指南</text>
      <text class="page-subtitle">选择最适合的 AI 魔法</text>
    </view>

    <scroll-view class="tab-scroll animate-fade-in-up" style="animation-delay: 0.1s;" scroll-x :show-scrollbar="false">
      <view class="tab-list">
        <view
          v-for="tab in tabs"
          :key="tab.id"
          class="tab-item"
          :class="{ active: currentTab === tab.id }"
          @tap="currentTab = tab.id"
        >
          <text class="tab-icon">{{ tab.emoji }}</text>
          <text class="tab-name">{{ tab.shortTitle }}</text>
        </view>
      </view>
    </scroll-view>

    <view class="tab-content" :key="currentTab">
      
      <view class="content-header animate-fade-in-up" style="animation-delay: 0.1s;">
        <text class="content-title">{{ activeData.title }}</text>
        <text class="content-subtitle">{{ activeData.subtitle }}</text>
        <view v-if="currentTab === 'time_engine'" class="engine-badge-inline">
          <text class="badge-dot"></text>
          <text class="badge-text">核心特色模块 · AI重绘您的照片</text>
        </view>
      </view>

      <view class="preview-section animate-fade-in-up" style="animation-delay: 0.2s;">
        <text class="section-label">效果预览</text>

        <view v-if="currentTab === 'voice'" class="feature-preview-card">
          <view class="feature-icon-wrap"><text class="f-icon">🎙️</text></view>
          <text class="feature-title">留音语音功能</text>
          <text class="feature-desc">支持文本转语音和声音复活两种模式</text>
          <view class="feature-modes">
            <view class="mode-card">
              <text class="mode-icon">⌨️</text>
              <text class="mode-name">文本转语音</text>
              <text class="mode-desc">输入文字生成自然语音</text>
            </view>
            <view class="mode-card">
              <text class="mode-icon">🎤</text>
              <text class="mode-name">声音复活</text>
              <text class="mode-desc">克隆相似回忆声音</text>
            </view>
          </view>
        </view>

        <view v-else-if="currentTab === 'liveportrait'" class="feature-preview-card">
          <view class="feature-icon-wrap"><text class="f-icon">🎬</text></view>
          <text class="feature-title">灵动人像功能</text>
          <text class="feature-desc">让静态照片动起来，重现当年的音容笑貌</text>
          <view class="feature-modes live-features">
            <view class="mode-card">
              <text class="mode-icon">😊</text>
              <text class="mode-name">表情生动</text>
            </view>
            <view class="mode-card">
              <text class="mode-icon">👤</text>
              <text class="mode-name">头部动作</text>
            </view>
            <view class="mode-card">
              <text class="mode-icon">🗣️</text>
              <text class="mode-name">口型同步</text>
            </view>
          </view>
        </view>

        <view v-else class="image-preview">
          <view class="preview-card float-hover">
            <image v-if="activeData.beforeImage" class="preview-img" :src="activeData.beforeImage" mode="aspectFill" />
            <view v-else class="preview-placeholder">
              <text class="preview-emoji">{{ activeData.emoji }}</text>
            </view>
            <view class="preview-label-wrap glassmorphism">
              <text class="preview-label">修复前</text>
            </view>
          </view>
          <view class="preview-arrow">
            <text class="arrow-text">→</text>
          </view>
          <view class="preview-card float-hover">
            <image v-if="activeData.afterImage" class="preview-img" :src="activeData.afterImage" mode="aspectFill" />
            <view v-else class="preview-placeholder">
              <text class="preview-emoji">{{ activeData.emoji }}</text>
            </view>
            <view class="preview-label-wrap glassmorphism">
              <text class="preview-label">修复后</text>
            </view>
          </view>
        </view>
      </view>

      <view class="scenes-section animate-fade-in-up" style="animation-delay: 0.3s;">
        <text class="section-label">适用场景</text>
        <view class="scenes-list">
          <view v-for="(scene, idx) in activeData.scenes" :key="idx" class="scene-item">
            <view class="scene-check-wrap"><text class="scene-check">✓</text></view>
            <text class="scene-text">{{ scene }}</text>
          </view>
        </view>
      </view>

      <view v-if="currentTab === 'time_engine'" class="tech-section animate-fade-in-up" style="animation-delay: 0.4s;">
        <text class="section-label">技术特点</text>
        <view class="tech-list">
          <view class="tech-card">
            <view class="tech-icon-wrap"><text class="tech-icon">🔗</text></view>
            <view class="tech-info">
              <text class="tech-name">节点工作流</text>
              <text class="tech-desc">基于ComfyUI的可视化节点编辑</text>
            </view>
          </view>
          <view class="tech-card">
            <view class="tech-icon-wrap"><text class="tech-icon">🧠</text></view>
            <view class="tech-info">
              <text class="tech-name">Flux模型引擎</text>
              <text class="tech-desc">采用Flux模型，支持8K超高清修复</text>
            </view>
          </view>
          <view class="tech-card">
            <view class="tech-icon-wrap"><text class="tech-icon">✨</text></view>
            <view class="tech-info">
              <text class="tech-name">智能理解修复</text>
              <text class="tech-desc">AI深度理解图像，创造性重绘</text>
            </view>
          </view>
        </view>
      </view>

      <view class="limitation-section animate-fade-in-up" style="animation-delay: 0.5s;">
        <view class="limitation-card">
          <view class="limitation-header">
            <text class="limitation-icon">⚠️</text>
            <text class="limitation-title">局限性与建议</text>
          </view>
          <text class="limitation-text">{{ activeData.limitations }}</text>
        </view>
      </view>

      <view class="try-section animate-fade-in-up" style="animation-delay: 0.6s;">
        <view class="try-btn" @tap="goWorkshop">
          <text class="try-text">前往修复 · {{ activeData.shortTitle }}</text>
          <text class="try-arrow">→</text>
        </view>
      </view>

    </view>

    <view style="height: 180rpx;"></view>

    <CustomTabBar :selected="3" />
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import CustomTabBar from '@/components/CustomTabBar.vue'
import { getToken } from '@/utils/request'

onMounted(() => {
  const token = getToken()
  if (!token) {
    uni.reLaunch({ url: '/pages/login/login' })
  }
})

const currentTab = ref('dustless_denoise')

interface TabData {
  id: string
  title: string
  shortTitle: string
  subtitle: string
  emoji: string
  beforeImage: string
  afterImage: string
  scenes: string[]
  limitations: string
  workshopModule: string
}

const tabs = [
  { id: 'dustless_denoise', shortTitle: '拂尘', emoji: '✨' },
  { id: 'liuguang', shortTitle: '流光', emoji: '🎨' },
  { id: 'qingying', shortTitle: '清影', emoji: '🔍' },
  { id: 'zhenrong', shortTitle: '真容', emoji: '👤' },
  { id: 'voice', shortTitle: '留音', emoji: '🎙️' },
  { id: 'liveportrait', shortTitle: '灵动', emoji: '🎬' },
  { id: 'time_engine', shortTitle: '时光引擎', emoji: '✦' }
]

const tabsData: Record<string, TabData> = {
  dustless_denoise: {
    id: 'dustless_denoise',
    title: '拂尘去痕',
    shortTitle: '拂尘',
    subtitle: '拂去岁月尘埃，重现往日洁净。智能去除照片中的划痕、污渍和瑕疵。',
    emoji: '✨',
    beforeImage: '/static/images/fuchen_before.png',
    afterImage: '/static/images/fuchen_after.jpg',
    scenes: [
      '老照片有折痕、划痕或裂纹',
      '照片表面有污渍、水渍或霉斑',
      '照片局部缺失或损坏',
      '需要去除照片上的印章或标注'
    ],
    limitations: '对于大面积缺失的区域，AI可能会生成不太准确的内容。建议优先处理物理损伤较小的照片，大面积缺失建议使用时光引擎模块。',
    workshopModule: 'dustless'
  },
  liuguang: {
    id: 'liuguang',
    title: '流光上色',
    shortTitle: '流光',
    subtitle: '点亮记忆光影，赋予画面新生。为黑白照片注入自然色彩。',
    emoji: '🎨',
    beforeImage: '/static/images/liuguang_before.jpg',
    afterImage: '/static/images/liuguang_after.jpg',
    scenes: [
      '黑白老照片需要恢复色彩',
      '褪色的彩色照片需要重新上色',
      '历史照片需要还原当时的色彩氛围',
      '想为珍贵回忆增添生动色彩'
    ],
    limitations: 'AI上色基于对场景的理解，颜色可能与原始真实色彩有差异。对于人物肤色等关键区域，建议多次尝试选择最佳效果。',
    workshopModule: 'liuguang'
  },
  qingying: {
    id: 'qingying',
    title: '清影清晰',
    shortTitle: '清影',
    subtitle: '重塑清晰轮廓，找回失落细节。智能提升照片清晰度。',
    emoji: '🔍',
    beforeImage: '/static/images/qingying_before.png',
    afterImage: '/static/images/qingying_after.jpg',
    scenes: [
      '模糊不清的老照片需要提升清晰度',
      '低分辨率照片需要放大并保持清晰',
      '噪点较多的照片需要降噪处理',
      '细节丢失的照片需要重建'
    ],
    limitations: '极度模糊的照片可能无法完全恢复清晰。AI会基于内容推断细节，可能与原始细节存在差异。',
    workshopModule: 'qingying'
  },
  zhenrong: {
    id: 'zhenrong',
    title: '真容修复',
    shortTitle: '真容',
    subtitle: '精修面部神态，还原至亲容颜。专业修复人物面部细节。',
    emoji: '👤',
    beforeImage: '/static/images/zhenrong_before.png',
    afterImage: '/static/images/zhenrong_after.jpg',
    scenes: [
      '人物面部模糊需要增强',
      '面部有划痕或损伤需要修复',
      '五官细节需要还原或增强',
      '全家福中人物面部需要修复'
    ],
    limitations: '面部修复效果受原始照片质量影响较大。如果面部区域缺失过多，修复结果可能与本人有差异。',
    workshopModule: 'zhenrong'
  },
  voice: {
    id: 'voice',
    title: '留音',
    shortTitle: '留音',
    subtitle: '让记忆中的声音穿越时空，再次在耳边响起。',
    emoji: '🎙️',
    beforeImage: '',
    afterImage: '',
    scenes: [
      '为老照片配上讲述者的声音',
      '克隆亲人的声音让回忆重现',
      '将文字日记转化为语音',
      '为家族影像添加旁白'
    ],
    limitations: '语音克隆需要提供足够长度的参考音频（建议10秒以上）。合成语音可能与原始声音存在细微差异。',
    workshopModule: 'voice'
  },
  liveportrait: {
    id: 'liveportrait',
    title: '灵动人像',
    shortTitle: '灵动',
    subtitle: '让静态照片动起来，赋予人像生动的表情和动作。',
    emoji: '🎬',
    beforeImage: '',
    afterImage: '',
    scenes: [
      '让老照片中的人物动起来',
      '为人物照片添加自然的表情变化',
      '配合音频让照片中的人物开口说话',
      '制作家族纪念视频'
    ],
    limitations: '灵动效果受原始照片角度和清晰度影响。侧面照片或遮挡较多的照片效果可能不理想。',
    workshopModule: 'live_portrait'
  },
  time_engine: {
    id: 'time_engine',
    title: '时光引擎',
    shortTitle: '时光引擎',
    subtitle: '基于Flux.1 Pro的AI一键修复，让老照片重获新生。',
    emoji: '✦',
    beforeImage: '/static/images/ai_engine_before.png',
    afterImage: '/static/images/ai_engine_after.png',
    scenes: [
      '严重受损的老照片需要全面修复',
      '需要同时修复多种问题（划痕+褪色+模糊）',
      '其他模块效果不理想时的终极方案',
      '追求最高质量修复效果'
    ],
    limitations: '时光引擎处理时间较长，需要耐心等待。由于使用生成式模型，修复结果可能存在创造性变化，与原始照片可能有细微差异。',
    workshopModule: 'time_engine'
  }
}

const activeData = computed(() => tabsData[currentTab.value] || tabsData['dustless_denoise'])

const goWorkshop = () => {
  uni.switchTab({ url: '/pages/workshop/workshop' })
}
</script>

<style lang="scss" scoped>
/* ================= 核心动画定义 ================= */
@keyframes fadeInUp {
  0% { opacity: 0; transform: translateY(40rpx) scale(0.98); }
  100% { opacity: 1; transform: translateY(0) scale(1); }
}

.animate-fade-in-up {
  opacity: 0;
  animation: fadeInUp 0.6s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
}

/* 弹簧交互反馈 */
.float-hover {
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.3s ease;
  &:active {
    transform: scale(0.95);
    box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.05);
  }
}

/* ================= 页面基础结构 ================= */
.help-page {
  min-height: 100vh;
  background: var(--bg-elegant, #FAF8F5);
  overflow-x: hidden;
}

.page-header {
  padding: 40rpx 40rpx 32rpx;
  .page-title {
    display: block; font-size: 60rpx; font-weight: 800;
    color: var(--text-main, #3D352B); letter-spacing: 2rpx;
  }
  .page-subtitle {
    display: block; font-size: 26rpx; color: var(--text-muted, #A39B90);
    margin-top: 16rpx; font-weight: 500;
  }
}

/* ================= Apple风格 药丸Tab ================= */
.tab-scroll {
  white-space: nowrap;
  padding: 0 40rpx 16rpx;
  margin-bottom: 32rpx;
}
.tab-list {
  display: inline-flex;
  gap: 20rpx;
  padding-right: 40rpx; /* 解决右侧滑不到底的留白 */
}
.tab-item {
  display: inline-flex;
  align-items: center;
  padding: 20rpx 40rpx;
  border-radius: 48rpx; /* 完美药丸 */
  background: #FFFFFF;
  border: 1rpx solid rgba(255, 255, 255, 0.9);
  box-shadow: 0 8rpx 24rpx rgba(0,0,0,0.03);
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);

  &.active {
    background: linear-gradient(135deg, var(--gold-main, #D4AF37), var(--champagne-main, #F2A97F));
    border-color: transparent;
    box-shadow: 0 12rpx 32rpx rgba(212, 175, 55, 0.25);
    transform: translateY(-4rpx);
    .tab-icon, .tab-name { color: #FFFFFF; }
  }

  .tab-icon { font-size: 36rpx; margin-right: 12rpx; transition: color 0.3s; }
  .tab-name { font-size: 28rpx; color: #5A4A32; font-weight: 700; transition: color 0.3s; }
}

/* ================= 动态内容区 ================= */
.tab-content {
  padding: 0 40rpx;
}

.content-header {
  margin-bottom: 48rpx;
  .content-title {
    display: block; font-size: 44rpx; font-weight: 800;
    color: var(--text-main, #3D352B); margin-bottom: 12rpx;
  }
  .content-subtitle {
    display: block; font-size: 28rpx; color: #8C7A5A; line-height: 1.6; font-weight: 500;
  }
  .engine-badge-inline {
    display: inline-flex; align-items: center; margin-top: 20rpx;
    background: rgba(212, 175, 55, 0.1); backdrop-filter: blur(10px);
    padding: 12rpx 24rpx; border-radius: 30rpx;
    .badge-dot { width: 12rpx; height: 12rpx; background: var(--gold-main); border-radius: 50%; margin-right: 12rpx; }
    .badge-text { font-size: 24rpx; color: var(--gold-dark, #B58D1F); font-weight: 700; }
  }
}

.section-label {
  display: block; font-size: 24rpx; font-weight: 800; color: var(--text-main);
  text-transform: uppercase; letter-spacing: 4rpx; margin-bottom: 24rpx; opacity: 0.8;
}

/* ================= 效果预览区 ================= */
.preview-section { margin-bottom: 48rpx; }

/* 沉浸式图片对比卡片 */
.image-preview {
  display: flex; align-items: center; gap: 24rpx;
}
.preview-card {
  flex: 1; border-radius: 40rpx; overflow: hidden; position: relative;
  background: #FFFFFF; box-shadow: 0 16rpx 40rpx rgba(0,0,0,0.04);
  .preview-img { width: 100%; height: 300rpx; display: block; }
  .preview-placeholder {
    width: 100%; height: 300rpx; display: flex; align-items: center; justify-content: center;
    background: #FDF8EF;
    .preview-emoji { font-size: 80rpx; filter: drop-shadow(0 8rpx 16rpx rgba(0,0,0,0.1)); }
  }
  /* 毛玻璃文字标签 */
  .preview-label-wrap {
    position: absolute; bottom: 20rpx; left: 50%; transform: translateX(-50%);
    background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
    padding: 10rpx 32rpx; border-radius: 40rpx; box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.05);
    border: 1rpx solid rgba(255,255,255,0.4);
    .preview-label { font-size: 24rpx; color: #5A4A32; font-weight: 800; letter-spacing: 2rpx; }
  }
}
.preview-arrow .arrow-text { font-size: 48rpx; color: var(--gold-main); font-weight: 800; text-shadow: 0 4rpx 8rpx rgba(212,175,55,0.2); }

/* 音视频高级卡片 (替代原本的蓝绿渐变) */
.feature-preview-card {
  background: linear-gradient(135deg, #FFFFFF, #FDF8EF);
  border-radius: 48rpx; padding: 48rpx 32rpx; text-align: center;
  box-shadow: 0 16rpx 40rpx rgba(212,175,55,0.05); border: 2rpx solid #FFFFFF;
  .feature-icon-wrap {
    width: 100rpx; height: 100rpx; background: #FFFFFF; border-radius: 50%;
    display: flex; align-items: center; justify-content: center; margin: 0 auto 24rpx;
    box-shadow: 0 12rpx 32rpx rgba(212,175,55,0.15); border: 1px solid rgba(212,175,55,0.1);
    .f-icon { font-size: 48rpx; }
  }
  .feature-title { display: block; font-size: 36rpx; font-weight: 800; color: #3D352B; margin-bottom: 12rpx; }
  .feature-desc { display: block; font-size: 26rpx; color: #8C7A5A; margin-bottom: 32rpx; line-height: 1.5; }
  
  .feature-modes { display: flex; gap: 20rpx; }
  .mode-card {
    flex: 1; background: rgba(255,255,255,0.7); backdrop-filter: blur(10px);
    border-radius: 32rpx; padding: 32rpx 20rpx; border: 1rpx solid #FFF;
    box-shadow: 0 8rpx 24rpx rgba(0,0,0,0.02);
    .mode-icon { display: block; font-size: 40rpx; margin-bottom: 16rpx; filter: drop-shadow(0 4rpx 8rpx rgba(0,0,0,0.05)); }
    .mode-name { display: block; font-size: 28rpx; font-weight: 800; color: #5A4A32; margin-bottom: 8rpx; }
    .mode-desc { display: block; font-size: 22rpx; color: #A39B90; line-height: 1.4; }
  }
}
.live-features .mode-card { padding: 24rpx 16rpx; }

/* ================= 适用场景 & 技术特点 ================= */
.scenes-section, .tech-section { margin-bottom: 48rpx; }

/* Apple 设置项风格列表 */
.scenes-list {
  background: #FFFFFF; border-radius: 40rpx; padding: 12rpx 0;
  box-shadow: 0 12rpx 40rpx rgba(0,0,0,0.03); border: 1rpx solid rgba(255,255,255,0.8);
}
.scene-item {
  display: flex; align-items: flex-start; gap: 20rpx; padding: 24rpx 32rpx;
  border-bottom: 1rpx solid #F5F0EB;
  &:last-child { border-bottom: none; }
  
  .scene-check-wrap {
    width: 40rpx; height: 40rpx; background: #FDF8EF; border-radius: 50%;
    display: flex; align-items: center; justify-content: center; margin-top: 2rpx;
    .scene-check { color: var(--gold-main); font-weight: 800; font-size: 22rpx; }
  }
  .scene-text { flex: 1; font-size: 28rpx; color: #5A4A32; font-weight: 600; line-height: 1.5; }
}

/* 技术特点卡片 */
.tech-list { display: flex; flex-direction: column; gap: 24rpx; }
.tech-card {
  display: flex; align-items: center; background: #FFFFFF; border-radius: 36rpx; padding: 32rpx;
  box-shadow: 0 12rpx 40rpx rgba(0,0,0,0.03); border: 1rpx solid rgba(255,255,255,0.8);
  .tech-icon-wrap {
    width: 88rpx; height: 88rpx; background: #FDF8EF; border-radius: 24rpx;
    display: flex; align-items: center; justify-content: center; margin-right: 24rpx;
    .tech-icon { font-size: 40rpx; }
  }
  .tech-info {
    flex: 1;
    .tech-name { display: block; font-size: 30rpx; font-weight: 800; color: #3D352B; margin-bottom: 6rpx; }
    .tech-desc { display: block; font-size: 24rpx; color: #8C7A5A; }
  }
}

/* ================= 局限性提示 (高级琥珀色) ================= */
.limitation-section { margin-bottom: 48rpx; }
.limitation-card {
  background: linear-gradient(135deg, #FFF9F0, #FFF4E5); border-radius: 36rpx; padding: 36rpx;
  border: 1rpx solid rgba(212, 175, 55, 0.2); box-shadow: 0 12rpx 32rpx rgba(212, 175, 55, 0.05);
  .limitation-header {
    display: flex; align-items: center; margin-bottom: 16rpx;
    .limitation-icon { font-size: 32rpx; margin-right: 12rpx; }
    .limitation-title { font-size: 28rpx; font-weight: 800; color: #B58D1F; }
  }
  .limitation-text { display: block; font-size: 26rpx; color: #9A7B4F; line-height: 1.6; font-weight: 500; }
}

/* ================= 立即尝试大按钮 ================= */
.try-section { margin-bottom: 40rpx; display: flex; justify-content: center; }
.try-btn {
  width: 100%; max-width: 600rpx;
  background: linear-gradient(135deg, var(--text-main, #3D352B), #1A1713);
  border-radius: 64rpx; padding: 36rpx 0;
  display: flex; align-items: center; justify-content: center; gap: 16rpx;
  box-shadow: 0 20rpx 40rpx rgba(44, 36, 23, 0.25);
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  
  &:active { transform: scale(0.96) translateY(4rpx); box-shadow: 0 10rpx 20rpx rgba(44, 36, 23, 0.15); }
  
  .try-text { font-size: 32rpx; color: var(--gold-light, #F5E4C3); font-weight: 800; letter-spacing: 2rpx; }
  .try-arrow { font-size: 36rpx; color: var(--gold-main); font-weight: 800; }
}
</style>
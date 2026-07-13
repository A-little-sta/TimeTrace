<template>
  <view class="workshop-page">
    <view class="page-header animate-fade-in-up" style="animation-delay: 0s;">
      <view class="header-top-row">
        <view class="header-text">
          <text class="page-title">修复工坊</text>
          <text class="page-subtitle">选择修复模块，让老照片重获新生</text>
        </view>
        <view class="user-area" @tap="toggleUserMenu">
          <view class="user-avatar">
            <image v-if="userAvatar" :src="userAvatar" mode="aspectFill" class="avatar-img"></image>
            <text v-else class="avatar-text">{{ userInitial }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 用户菜单弹出层 -->
    <view v-if="showUserMenu" class="user-menu-mask" @tap="showUserMenu = false">
      <view class="user-menu" @tap.stop>
        <view class="menu-user-info">
          <view class="menu-avatar">
            <image v-if="userAvatar" :src="userAvatar" mode="aspectFill" class="menu-avatar-img"></image>
            <text v-else class="menu-avatar-text">{{ userInitial }}</text>
          </view>
          <view class="menu-user-detail">
            <text class="menu-username">{{ username }}</text>
            <text class="menu-email">{{ userEmail }}</text>
          </view>
        </view>
        <view class="menu-divider"></view>
        <view class="menu-item" @tap="handleLogout">
          <text class="menu-item-icon">&#x1F6AA;</text>
          <text class="menu-item-text">退出登录</text>
        </view>
      </view>
    </view>

    <view class="time-engine-card animate-fade-in-up float-breathing" style="animation-delay: 0.1s;" @tap="goModule('time_engine')">
      <view class="shimmer-effect"></view>
      <view class="engine-badge">核心特色</view>
      <view class="engine-content">
        <view class="engine-icon-wrap">
          <text class="engine-icon-text">✦</text>
        </view>
        <view class="engine-info">
          <text class="engine-name">时光引擎</text>
          <text class="engine-desc">基于Flux.1 Pro的AI一键修复，让老照片重获新生</text>
        </view>
      </view>
      <view class="engine-features">
        <view class="engine-feature">
          <text class="feature-dot"></text>
          <text class="feature-text">Flux.1 Pro超强模型</text>
        </view>
        <view class="engine-feature">
          <text class="feature-dot"></text>
          <text class="feature-text">ComfyUI节点工作流</text>
        </view>
        <view class="engine-feature">
          <text class="feature-dot"></text>
          <text class="feature-text">智能多维度修复</text>
        </view>
      </view>
    </view>

    <view class="section-title animate-fade-in-up" style="animation-delay: 0.2s;">
      <view class="section-line"></view>
      <text class="section-text">图片修复</text>
      <view class="section-line"></view>
    </view>

    <view class="module-grid">
      <view class="module-card animate-fade-in-up" style="animation-delay: 0.3s;" @tap="goModule('dustless')">
        <view class="card-watermark"><text class="icon-emoji">✨</text></view>
        
        <view class="card-top">
          <view class="module-icon icon-dustless"><text class="icon-emoji">✨</text></view>
          <view class="card-arrow"><text>→</text></view>
        </view>
        <view class="card-bottom">
          <text class="module-name">拂尘修复</text>
          <text class="module-desc">去除划痕污渍</text>
        </view>
      </view>

      <view class="module-card animate-fade-in-up" style="animation-delay: 0.4s;" @tap="goModule('liuguang')">
        <view class="card-watermark"><text class="icon-emoji">🎨</text></view>
        
        <view class="card-top">
          <view class="module-icon icon-liuguang"><text class="icon-emoji">🎨</text></view>
          <view class="card-arrow"><text>→</text></view>
        </view>
        <view class="card-bottom">
          <text class="module-name">流光上色</text>
          <text class="module-desc">黑白照片上色</text>
        </view>
      </view>

      <view class="module-card animate-fade-in-up" style="animation-delay: 0.5s;" @tap="goModule('qingying')">
        <view class="card-watermark"><text class="icon-emoji">🔍</text></view>
        
        <view class="card-top">
          <view class="module-icon icon-qingying"><text class="icon-emoji">🔍</text></view>
          <view class="card-arrow"><text>→</text></view>
        </view>
        <view class="card-bottom">
          <text class="module-name">清影清晰</text>
          <text class="module-desc">提升照片清晰度</text>
        </view>
      </view>

      <view class="module-card animate-fade-in-up" style="animation-delay: 0.6s;" @tap="goModule('zhenrong')">
        <view class="card-watermark"><text class="icon-emoji">👤</text></view>
        
        <view class="card-top">
          <view class="module-icon icon-zhenrong"><text class="icon-emoji">👤</text></view>
          <view class="card-arrow"><text>→</text></view>
        </view>
        <view class="card-bottom">
          <text class="module-name">真容修复</text>
          <text class="module-desc">精修面部细节</text>
        </view>
      </view>
    </view>

    <view class="section-title animate-fade-in-up" style="animation-delay: 0.7s;">
      <view class="section-line"></view>
      <text class="section-text">音频修复</text>
      <view class="section-line"></view>
    </view>

    <view class="module-grid">
      <view class="module-card animate-fade-in-up" style="animation-delay: 0.75s;" @tap="goModule('voice')">
        <view class="card-watermark"><text class="icon-emoji">🎙️</text></view>
        
        <view class="card-top">
          <view class="module-icon icon-voice"><text class="icon-emoji">🎙️</text></view>
          <view class="card-arrow"><text>→</text></view>
        </view>
        <view class="card-bottom">
          <text class="module-name">留音</text>
          <text class="module-desc">语音合成与克隆</text>
        </view>
      </view>
    </view>

    <view class="section-title animate-fade-in-up" style="animation-delay: 0.85s;">
      <view class="section-line"></view>
      <text class="section-text">视频修复</text>
      <view class="section-line"></view>
    </view>

    <view class="module-grid">
      <view class="module-card animate-fade-in-up" style="animation-delay: 0.9s;" @tap="goModule('live_portrait')">
        <view class="card-watermark"><text class="icon-emoji">🎬</text></view>
        
        <view class="card-top">
          <view class="module-icon icon-live"><text class="icon-emoji">🎬</text></view>
          <view class="card-arrow"><text>→</text></view>
        </view>
        <view class="card-bottom">
          <text class="module-name">灵动人像</text>
          <text class="module-desc">人像动态复活</text>
        </view>
      </view>
    </view>

    <view style="height: 180rpx;"></view>

    <CustomTabBar :selected="0" />
  </view>
</template>

<script setup lang="ts">
import CustomTabBar from '@/components/CustomTabBar.vue'
import { getToken, removeToken, getUserInfo, removeUserInfo } from '@/utils/request'
import { ref, computed, onMounted } from 'vue'

const showUserMenu = ref(false)
const username = ref('')
const userEmail = ref('')
const userAvatar = ref('')

const userInitial = computed(() => {
  return username.value ? username.value.charAt(0).toUpperCase() : 'U'
})

onMounted(() => {
  const token = getToken()
  if (!token) {
    uni.reLaunch({ url: '/pages/login/login' })
    return
  }
  const user = getUserInfo()
  if (user) {
    username.value = user.username || ''
    userEmail.value = user.email || ''
    userAvatar.value = user.wechat_avatar || ''
  }
})

const toggleUserMenu = () => {
  showUserMenu.value = !showUserMenu.value
}

const handleLogout = () => {
  showUserMenu.value = false
  uni.showModal({
    title: '退出登录',
    content: '确定要退出当前账号吗？',
    confirmColor: '#D4AF37',
    success: (res) => {
      if (res.confirm) {
        removeToken()
        removeUserInfo()
        uni.reLaunch({ url: '/pages/login/login' })
      }
    }
  })
}

const goModule = (moduleId: string) => {
  uni.navigateTo({
    url: `/pages/workshop/module?id=${moduleId}`
  })
}
</script>

<style lang="scss" scoped>
/* ================= 核心动画定义 ================= */
@keyframes fadeInUp {
  0% { opacity: 0; transform: translateY(40rpx) scale(0.98); }
  100% { opacity: 1; transform: translateY(0) scale(1); }
}

@keyframes floatBreathing {
  0%, 100% { transform: translateY(0); box-shadow: 0 20rpx 50rpx rgba(212, 175, 55, 0.12); }
  50% { transform: translateY(-8rpx); box-shadow: 0 28rpx 64rpx rgba(212, 175, 55, 0.2); }
}

@keyframes shimmer {
  0% { transform: translateX(-150%) skewX(-30deg); }
  100% { transform: translateX(200%) skewX(-30deg); }
}

.animate-fade-in-up {
  opacity: 0;
  animation: fadeInUp 0.7s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
}

.float-breathing {
  animation: fadeInUp 0.7s cubic-bezier(0.2, 0.8, 0.2, 1) forwards,
             floatBreathing 6s ease-in-out 0.7s infinite;
}

/* ================= 页面基础结构 ================= */
.workshop-page {
  min-height: 100vh;
  background: var(--bg-elegant, #FAF8F5);
  padding: 0 40rpx; 
  overflow-x: hidden;
}

.page-header {
  padding: 40rpx 0 48rpx;
  .header-top-row {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
  }
  .header-text { flex: 1; }
  .page-title {
    display: block; font-size: 60rpx; font-weight: 800;
    color: var(--text-main, #3D352B); letter-spacing: 2rpx;
  }
  .page-subtitle {
    display: block; font-size: 26rpx; color: var(--text-muted, #A39B90);
    margin-top: 16rpx; font-weight: 500;
  }
  .user-area { padding: 8rpx; }
  .user-avatar {
    width: 80rpx;
    height: 80rpx;
    border-radius: 50%;
    background: linear-gradient(135deg, #D4AF37, #F2A97F);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 8rpx 24rpx rgba(212, 175, 55, 0.2);
    overflow: hidden;
  }
  .avatar-img {
    width: 100%;
    height: 100%;
    border-radius: 50%;
  }
  .avatar-text {
    font-size: 36rpx;
    font-weight: 800;
    color: #FFFFFF;
  }
}

/* ================= 用户菜单弹出层 ================= */
.user-menu-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.3);
  z-index: 999;
  display: flex;
  justify-content: flex-end;
  padding: 120rpx 40rpx 0 0;
}

.user-menu {
  width: 480rpx;
  background: #FFFFFF;
  border-radius: 32rpx;
  box-shadow: 0 24rpx 64rpx rgba(0, 0, 0, 0.12);
  overflow: hidden;
  animation: menuSlideIn 0.25s ease;
}

@keyframes menuSlideIn {
  0% { opacity: 0; transform: translateY(-20rpx) scale(0.95); }
  100% { opacity: 1; transform: translateY(0) scale(1); }
}

.menu-user-info {
  display: flex;
  align-items: center;
  padding: 40rpx 36rpx;
}

.menu-avatar {
  width: 88rpx;
  height: 88rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #D4AF37, #F2A97F);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 24rpx;
  flex-shrink: 0;
  overflow: hidden;
}

.menu-avatar-img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
}

.menu-avatar-text {
  font-size: 40rpx;
  font-weight: 800;
  color: #FFFFFF;
}

.menu-user-detail { flex: 1; overflow: hidden; }

.menu-username {
  display: block;
  font-size: 32rpx;
  font-weight: 700;
  color: #3D352B;
}

.menu-email {
  display: block;
  font-size: 24rpx;
  color: #A39B90;
  margin-top: 6rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.menu-divider {
  height: 1rpx;
  background: #F0ECE4;
  margin: 0 36rpx;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 36rpx 40rpx;
  transition: background 0.2s;

  &:active { background: #FAF8F5; }
}

.menu-item-icon { font-size: 36rpx; margin-right: 20rpx; }

.menu-item-text {
  font-size: 30rpx;
  color: #E53E3E;
  font-weight: 600;
}

/* ================= 时光引擎卡片 ================= */
.time-engine-card {
  box-sizing: border-box;
  position: relative;
  background: linear-gradient(135deg, #FFFFFF 0%, #FDF8EF 50%, #F5E4C3 100%);
  border-radius: 48rpx;
  padding: 48rpx 40rpx;
  margin-bottom: 56rpx;
  border: 2rpx solid rgba(255, 255, 255, 0.9);
  overflow: hidden; 
  transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.2s ease;

  &:active {
    transform: scale(0.96) translateY(4rpx);
    box-shadow: 0 10rpx 20rpx rgba(212, 175, 55, 0.1) !important;
  }

  .shimmer-effect {
    position: absolute; top: 0; left: 0; width: 30%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.8), transparent);
    z-index: 1; pointer-events: none;
    animation: shimmer 4s cubic-bezier(0.4, 0, 0.2, 1) infinite;
    animation-delay: 2s; 
  }

  .engine-badge {
    position: absolute; top: 0; right: 0;
    background: linear-gradient(135deg, var(--gold-main, #D4AF37), var(--champagne-main, #F2A97F));
    color: #FFFFFF; font-size: 22rpx; font-weight: 700; padding: 12rpx 32rpx;
    border-radius: 0 48rpx 0 28rpx; box-shadow: -4rpx 4rpx 20rpx rgba(212, 175, 55, 0.25); z-index: 2;
  }

  .engine-content {
    display: flex; align-items: center; margin-bottom: 32rpx; position: relative; z-index: 2;
  }

  .engine-icon-wrap {
    width: 104rpx; height: 104rpx; background: linear-gradient(135deg, var(--gold-main, #D4AF37), #FCE8D5);
    border-radius: 32rpx; display: flex; align-items: center; justify-content: center; margin-right: 28rpx;
    box-shadow: 0 12rpx 32rpx rgba(212, 175, 55, 0.3), inset 0 4rpx 8rpx rgba(255,255,255,0.4);
    .engine-icon-text { font-size: 52rpx; color: #fff; text-shadow: 0 4rpx 8rpx rgba(0,0,0,0.1); }
  }

  .engine-info {
    flex: 1;
    .engine-name { display: block; font-size: 40rpx; font-weight: 800; color: #5A4A32; margin-bottom: 8rpx; }
    .engine-desc { display: block; font-size: 24rpx; color: #8C7A5A; line-height: 1.4; }
  }

  .engine-features { display: flex; flex-wrap: wrap; gap: 16rpx; position: relative; z-index: 2; }
  .engine-feature {
    display: flex; align-items: center; background: rgba(255, 255, 255, 0.6); backdrop-filter: blur(12px);
    border: 1rpx solid rgba(255,255,255,0.8); padding: 12rpx 24rpx; border-radius: 30rpx;
    .feature-dot {
      width: 12rpx; height: 12rpx; background: linear-gradient(135deg, var(--gold-main), var(--champagne-main));
      border-radius: 50%; margin-right: 12rpx; box-shadow: 0 2rpx 6rpx rgba(212, 175, 55, 0.4);
    }
    .feature-text { font-size: 22rpx; color: #6A5B42; font-weight: 700; }
  }
}

/* ================= 分类标题 ================= */
.section-title {
  display: flex; align-items: center; margin-bottom: 36rpx;
  .section-line { flex: 1; height: 2rpx; background: linear-gradient(90deg, transparent, rgba(212, 175, 55, 0.25), transparent); }
  .section-text { padding: 0 28rpx; font-size: 26rpx; color: var(--text-muted, #A39B90); font-weight: 800; letter-spacing: 6rpx; text-transform: uppercase; }
}

/* ================= 模块网格与卡片 (核心重构区) ================= */
.module-grid {
  display: flex; flex-wrap: wrap; gap: 24rpx; margin-bottom: 56rpx;
}

.module-card {
  box-sizing: border-box; /* 这个绝对不能丢，修复挤作一团的元凶 */
  width: calc(50% - 12rpx); /* 精确计算两列宽度 */
  background: var(--bg-card, #FFFFFF);
  border-radius: 40rpx;
  padding: 36rpx 32rpx;
  display: flex;
  flex-direction: column;
  align-items: flex-start; /* 改为左对齐，布局更显空间感 */
  position: relative;
  overflow: hidden; 
  border: 2rpx solid rgba(255, 255, 255, 0.9);
  box-shadow: 0 12rpx 40rpx rgba(0, 0, 0, 0.03);
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);

  &:active {
    transform: scale(0.92) translateY(6rpx);
    box-shadow: 0 4rpx 12rpx rgba(212, 175, 55, 0.06);
    background: #FDFBF8;
  }
}

/* 高级感背景水印 */
.card-watermark {
  position: absolute;
  right: -24rpx;
  bottom: -24rpx;
  opacity: 0.05; /* 若隐若现 */
  transform: rotate(-20deg);
  pointer-events: none;
  z-index: 1;
  .icon-emoji { font-size: 180rpx; } /* 巨大化 */
}

/* 顶部区域 (图标 + 引导箭头) */
.card-top {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32rpx;
  position: relative;
  z-index: 2;
}

.module-icon {
  width: 96rpx; height: 96rpx; border-radius: 30rpx;
  display: flex; align-items: center; justify-content: center;
  box-shadow: inset 0 0 20rpx rgba(255, 255, 255, 0.8), 0 8rpx 24rpx rgba(0,0,0,0.02);
  border: 1rpx solid rgba(255,255,255,0.6);
  .icon-emoji { font-size: 44rpx; filter: drop-shadow(0 4rpx 8rpx rgba(0,0,0,0.08)); }
}

/* 各个模块的高级微渐变底色 */
.icon-dustless { background: linear-gradient(135deg, #FDFBF8, #F5EBE1); }
.icon-liuguang { background: linear-gradient(135deg, #FFFCF5, #FDE6C5); }
.icon-qingying { background: linear-gradient(135deg, #F4FAFF, #E1F0FA); }
.icon-zhenrong { background: linear-gradient(135deg, #FFF7F8, #FAD6DF); }
.icon-voice    { background: linear-gradient(135deg, #F2FCF8, #DDF3E8); }
.icon-live     { background: linear-gradient(135deg, #F9F7FF, #E7DDF9); }

/* 右上角进入箭头 */
.card-arrow {
  width: 44rpx; height: 44rpx; border-radius: 50%;
  background: var(--bg-elegant, #FAF8F5);
  display: flex; align-items: center; justify-content: center;
  color: var(--gold-main, #D4AF37); font-size: 24rpx; font-weight: 800;
  box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.04);
}

/* 底部文字区域 */
.card-bottom {
  position: relative;
  z-index: 2;
}

.module-name {
  display: block; font-size: 32rpx; font-weight: 800;
  color: var(--text-main, #3D352B); margin-bottom: 8rpx;
}

.module-desc {
  display: block; font-size: 22rpx; color: var(--text-muted, #A39B90); font-weight: 500;
}
</style>
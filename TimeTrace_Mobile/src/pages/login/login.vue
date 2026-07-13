<template>
  <view class="login-page">
    <view class="header-bg">
      <view class="header-pattern animate-fade-in-down" style="animation-delay: 0s;"></view>
      <view class="shimmer-light animate-fade-in-down" style="animation-delay: 0.1s;"></view>
      
      <view class="header-content animate-fade-in-down" style="animation-delay: 0.2s;">
        <view class="icon-wrap float-breathing">
          <image src="/static/images/logo.png" mode="aspectFill" class="logo-img"></image>
        </view>
        <text class="header-title">岁月笺影</text>
        <text class="header-subtitle">为您重拾流光，留驻温情</text>
      </view>
    </view>

    <view class="form-area animate-fade-in-up" style="animation-delay: 0.4s;">
      
      <view class="input-group">
        <text class="input-label">用户名</text>
        <view class="input-wrap" :class="{ 'input-focus': focusEmail }">
          <text class="input-icon">👤</text>
          <input 
            type="text" 
            v-model="email" 
            placeholder="请输入您的用户名" 
            placeholder-class="placeholder-style"
            @focus="focusEmail = true"
            @blur="focusEmail = false"
          />
        </view>
      </view>

      <view class="input-group">
        <text class="input-label">密码</text>
        <view class="input-wrap" :class="{ 'input-focus': focusPassword }">
          <text class="input-icon">🔒</text>
          <input 
            type="password" 
            v-model="password" 
            placeholder="请输入您的密码" 
            placeholder-class="placeholder-style"
            @focus="focusPassword = true"
            @blur="focusPassword = false"
          />
        </view>
      </view>

      <view class="try-section animate-fade-in-up" style="animation-delay: 0.6s;">
        <view class="login-btn try-btn" @tap="login">
          <view class="shimmer-effect"></view>
          <text class="btn-text">立即登录</text>
          <text class="btn-arrow">→</text>
        </view>
      </view>

      <view class="guide-area animate-fade-in-up" style="animation-delay: 0.7s;">
        <view class="register-guide" @tap="register">
          <text class="guide-text">还没有账号?</text>
          <text class="guide-link">前往注册</text>
        </view>
      </view>

    </view>

    <view class="social-login animate-fade-in-up" style="animation-delay: 0.8s;">
      <view class="social-divider">
        <view class="divider-line"></view>
        <text class="divider-text">社交账号快捷登录</text>
        <view class="divider-line"></view>
      </view>
      
      <view class="social-icons">
        <view class="social-item float-hover" @tap="notImplemented">
          <view class="social-icon-wrap wx-icon">
            <text class="social-icon-text">微</text>
          </view>
        </view>
        <view class="social-item float-hover" @tap="notImplemented">
          <view class="social-icon-wrap qq-icon">
            <text class="social-icon-text">Q</text>
          </view>
        </view>
        <view class="social-item float-hover" @tap="notImplemented">
          <view class="social-icon-wrap mail-icon">
            <text class="social-icon-text">✉</text>
          </view>
        </view>
      </view>
    </view>

    <view style="height: 60rpx;"></view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { getToken, setToken, setUserInfo, postForm } from '@/utils/request';

// 已登录则直接跳转工坊
onMounted(() => {
  const token = getToken()
  if (token) {
    uni.switchTab({ url: '/pages/workshop/workshop' })
  }
})

// ==================== 邮箱登录（非微信平台） ====================
const email = ref('');
const password = ref('');
const focusEmail = ref(false);
const focusPassword = ref(false);
const isLoading = ref(false);
const errorMessage = ref('');

const login = async () => {
  errorMessage.value = ''
  if (!email.value.trim()) { errorMessage.value = '请输入用户名'; return }
  if (!password.value) { errorMessage.value = '请输入密码'; return }

  isLoading.value = true
  try {
    const res = await postForm<{
      access_token: string
      token_type: string
      user: { id: number; username: string; email: string }
    }>('/auth/login', {
      username: email.value.trim(),
      password: password.value,
    })
    setToken(res.access_token)
    setUserInfo(res.user)
    uni.showToast({ title: '登录成功', icon: 'success' })
    setTimeout(() => { uni.switchTab({ url: '/pages/workshop/workshop' }) }, 1000)
  } catch (error) {
    const err = error as Error
    const msg = err.message || ''
    if (msg.includes('用户名或密码错误') || msg.includes('Incorrect')) {
      uni.showToast({ title: '用户名或密码错误', icon: 'none' })
    } else if (msg.includes('网络')) {
      uni.showToast({ title: '网络连接失败', icon: 'none' })
    } else {
      uni.showToast({ title: msg || '登录失败', icon: 'none' })
    }
  } finally {
    isLoading.value = false
  }
};

const register = () => {
  uni.navigateTo({ url: '/pages/register/register' });
};

const notImplemented = () => {
  uni.showToast({ title: '该功能暂未开放', icon: 'none' });
};
</script>

<style lang="scss" scoped>
/* ================= 核心动画定义 ================= */
@keyframes fadeInUp {
  0% { opacity: 0; transform: translateY(40rpx) scale(0.98); }
  100% { opacity: 1; transform: translateY(0) scale(1); }
}

@keyframes fadeInDown {
  0% { opacity: 0; transform: translateY(-40rpx) scale(0.98); }
  100% { opacity: 1; transform: translateY(0) scale(1); }
}

@keyframes floatBreathing {
  0%, 100% { transform: translateY(0); box-shadow: 0 16rpx 40rpx rgba(212, 175, 55, 0.15); }
  50% { transform: translateY(-8rpx); box-shadow: 0 24rpx 64rpx rgba(212, 175, 55, 0.25); }
}

@keyframes shimmer {
  0% { transform: translateX(-150%) skewX(-30deg); }
  100% { transform: translateX(200%) skewX(-30deg); }
}

.animate-fade-in-up {
  opacity: 0;
  animation: fadeInUp 0.7s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
}

.animate-fade-in-down {
  opacity: 0;
  animation: fadeInDown 0.7s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
}

.float-breathing {
  animation: floatBreathing 6s ease-in-out infinite;
}

.float-hover {
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.3s ease;
  &:active {
    transform: scale(0.92) translateY(4rpx);
    box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.06) !important;
  }
}

/* ================= 页面基础结构 ================= */
.login-page {
  min-height: 100vh;
  background: var(--bg-elegant, #FFFFFF);
  display: flex;
  flex-direction: column;
  overflow-x: hidden;
}

/* 顶部装饰区域 */
.header-bg {
  position: relative;
  /* 修复：加高了背景高度，给文字留出充足空间 */
  height: 580rpx;
  background: linear-gradient(135deg, #F9F1E0 0%, #FAF8F5 50%, #F5E4C3 100%);
  overflow: hidden;
  border-radius: 0 0 100rpx 100rpx;
  box-shadow: 0 20rpx 60rpx rgba(212, 175, 55, 0.1);
  margin-bottom: -40rpx;
}

.header-pattern {
  position: absolute; top: -100rpx; right: -120rpx; width: 500rpx; height: 500rpx; border-radius: 50%;
  background: radial-gradient(circle, rgba(212, 175, 55, 0.15) 0%, rgba(255,255,255,0) 70%);
}

.shimmer-light {
  position: absolute; top: 10rpx; left: -100rpx; width: 400rpx; height: 400rpx; border-radius: 50%;
  background: radial-gradient(circle, rgba(242, 169, 127, 0.15) 0%, rgba(255,255,255,0) 70%);
}

.header-content {
  position: relative; z-index: 2; display: flex; flex-direction: column; align-items: center; justify-content: center;
  height: 100%; padding-top: 40rpx;
}

/* 修复：Logo容器缩小，取消了原本夸张的180%缩放，显得更精致 */
.icon-wrap {
  width: 180rpx; height: 180rpx; border-radius: 56rpx;
  background: #FFFFFF;
  display: flex; align-items: center; justify-content: center; margin-bottom: 24rpx;
  border: none;
  box-shadow: 0 16rpx 48rpx rgba(212, 175, 55, 0.15);
  overflow: hidden;
}
.logo-img { width: 100%; height: 100%; }

.header-title {
  font-size: 56rpx; font-weight: 800; color: #5A4A32; letter-spacing: 4rpx; margin-bottom: 12rpx;
  text-shadow: 0 4rpx 16rpx rgba(212,175,55,0.1);
}

.header-subtitle {
  font-size: 26rpx; color: rgba(163, 155, 144, 0.9); font-weight: 500;
}

/* ================= 登录表单悬浮区 ================= */
.form-area {
  position: relative; z-index: 10; margin: 0 48rpx 48rpx; padding: 60rpx 48rpx 40rpx;
  background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px);
  border-radius: 48rpx; border: 1rpx solid rgba(255, 255, 255, 0.5);
  box-shadow: 0 32rpx 80rpx rgba(44, 36, 23, 0.05);
}

.input-group { margin-bottom: 40rpx; }
.input-label {
  display: block; font-size: 26rpx; font-weight: 800; color: #5A4A32;
  margin-bottom: 16rpx; padding-left: 16rpx; letter-spacing: 2rpx; text-transform: uppercase;
}

.input-wrap {
  display: flex; align-items: center;
  background-color: #FAF8F5;
  border-radius: 36rpx; padding: 0 32rpx; height: 112rpx;
  transition: all 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);
  box-shadow: inset 0 2rpx 6rpx rgba(0,0,0,0.02);
  border: 2rpx solid transparent;
}

.input-wrap.input-focus {
  background-color: #FFFFFF;
  border-color: rgba(212, 175, 55, 0.5);
  box-shadow: 0 12rpx 32rpx rgba(212, 175, 55, 0.1);
  transform: translateY(-2rpx);
  .input-icon { color: var(--gold-main); opacity: 1; }
}

.input-icon { font-size: 40rpx; margin-right: 20rpx; color: #C2BBB2; transition: color 0.3s; }
.input-wrap input {
  flex: 1; font-size: 32rpx; color: #3D352B; font-weight: 600;
  ::placeholder { font-weight: 400; color: #C2BBB2; }
}
.placeholder-style { color: #C2BBB2; font-weight: 400; }

/* ================= 按钮通用 ================= */
.try-section { margin-bottom: 40rpx; }

.login-btn {
  width: 100%; height: 112rpx; border-radius: 56rpx;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 16rpx 40rpx rgba(212, 175, 55, 0.3);
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.3s ease;
  overflow: hidden; position: relative;

  &:active {
    transform: scale(0.96) translateY(4rpx);
    box-shadow: 0 8rpx 20rpx rgba(212, 175, 55, 0.2) !important;
  }
}

.try-btn {
  background: linear-gradient(135deg, var(--gold-main, #D4AF37), var(--champagne-main, #F2A97F));
}

.shimmer-effect {
  position: absolute; top: 0; left: 0; width: 30%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.8), transparent);
  z-index: 1; pointer-events: none;
  animation: shimmer 4s cubic-bezier(0.4, 0, 0.2, 1) infinite; animation-delay: 2s;
}

.btn-text { font-size: 36rpx; font-weight: 800; color: #FFFFFF; letter-spacing: 12rpx; padding-left: 12rpx; position: relative; z-index: 2; }
.btn-arrow { font-size: 36rpx; color: #FFFFFF; font-weight: 800; margin-left: 20rpx; position: relative; z-index: 2; }

/* ================= 注册引导 ================= */
.register-guide {
  display: flex; align-items: center; justify-content: center; margin-top: 20rpx; padding: 10rpx 0;
}
.guide-text { font-size: 28rpx; color: var(--text-muted, #A39B90); font-weight: 500; }
.guide-link {
  font-size: 28rpx; color: var(--gold-dark, #D4AF37); font-weight: 800;
  margin-left: 12rpx; transition: color 0.3s;
  &:active { color: var(--champagne-main); }
}

/* ================= 第三方登录 (修复：App 级标准圆形样式) ================= */
.social-login { padding: 0 48rpx; margin-top: 20rpx; }

.social-divider {
  display: flex; align-items: center; justify-content: center; margin-bottom: 40rpx;
  .divider-line { flex: 1; height: 1rpx; background-color: rgba(212, 175, 55, 0.15); }
  .divider-text { padding: 0 30rpx; font-size: 24rpx; color: #C2BBB2; font-weight: 600; letter-spacing: 2rpx; }
}

.social-icons { display: flex; justify-content: center; gap: 56rpx; }
.social-item {
  width: 104rpx; height: 104rpx; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  background: #FFFFFF;
  box-shadow: 0 8rpx 24rpx rgba(212, 175, 55, 0.1);
  border: 1rpx solid rgba(255, 255, 255, 0.9);
  position: relative;
  transition: all 0.3s ease;
  
  &:active {
    background: #FDFBF8;
    box-shadow: 0 4rpx 12rpx rgba(212, 175, 55, 0.05);
  }
}

.social-icon-wrap {
  width: 72rpx; height: 72rpx; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  .social-icon-text { font-size: 36rpx; font-weight: 800; color: #FFFFFF; }
  &.wx-icon  { background: linear-gradient(135deg, #07C160, #06AD56); }
  &.qq-icon  { background: linear-gradient(135deg, #12B7F5, #0D8ED9); }
  &.mail-icon { background: linear-gradient(135deg, #FF6B6B, #EE5A24); }
}
</style>
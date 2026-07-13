<template>
  <view class="gallery-page">
    <view class="ambient-background">
      <view class="orb orb-gold"></view>
      <view class="orb orb-champagne"></view>
      <view class="orb orb-white"></view>
    </view>

    <view class="page-header animate-fade-in-up" style="animation-delay: 0s;">
      <view class="header-top">
        <view>
          <text class="page-title">时光图库</text>
          <text class="page-subtitle">珍藏每一刻回忆，让瞬间成为永恒</text>
        </view>
        <view class="header-actions">
          <view v-if="photos.length > 0 && !isSelectMode" class="action-btn glass-btn float-hover" @tap="enterSelectMode">
            <text class="action-text">选择</text>
          </view>
        </view>
      </view>
    </view>

    <view v-if="isSelectMode" class="select-bar-wrapper animate-fade-in-up">
      <view class="select-bar glass-panel">
        <view class="select-info">
          <text class="select-count">{{ selectedPhotoIds.length }}/{{ photos.length }} 已选择</text>
          <view class="select-all-btn float-hover" @tap="toggleSelectAll">
            <text>{{ selectedPhotoIds.length === photos.length ? '取消全选' : '全选' }}</text>
          </view>
        </view>
        <view class="select-actions">
          <view class="cancel-btn float-hover" @tap="exitSelectMode">
            <text>取消</text>
          </view>
          <view class="delete-btn float-hover" :class="{ disabled: selectedPhotoIds.length === 0 }" @tap="batchDelete">
            <text>删除({{ selectedPhotoIds.length }})</text>
          </view>
        </view>
      </view>
    </view>

    <view class="photo-grid">
      <view class="upload-card glass-panel float-hover animate-fade-in-up" style="animation-delay: 0.1s;" @tap="triggerUpload">
        <view class="upload-icon-wrap float-breathing">
          <text v-if="isUploading" class="upload-loading">⏳</text>
          <text v-else class="upload-plus">✦</text>
        </view>
        <text class="upload-text">{{ isUploading ? '时光加载中...' : '上传影像' }}</text>
        <text class="upload-hint">支持 JPG, PNG 高清上传</text>
      </view>

      <view
        v-for="(photo, index) in photos"
        :key="photo.id"
        class="photo-card float-hover animate-fade-in-up"
        :style="{ animationDelay: `${0.15 + (index % 10) * 0.05}s` }"
        :class="{ selected: selectedPhotoIds.includes(photo.id) }"
        @tap="onPhotoTap(photo)"
      >
        <view v-if="isSelectMode" class="check-box" :class="{ checked: selectedPhotoIds.includes(photo.id) }">
          <text v-if="selectedPhotoIds.includes(photo.id)" class="check-mark">✓</text>
        </view>
        
        <image class="photo-img" :src="photo.url" mode="aspectFill" lazy-load />
        
        <view v-if="!isSelectMode" class="photo-overlay glass-overlay">
          <text class="photo-filename">{{ photo.filename }}</text>
          <view class="photo-actions">
            <view class="photo-action-btn repair-btn" @tap.stop="goToRepair(photo)">
              <text>修复</text>
            </view>
            <view class="photo-action-btn delete-action-btn" @tap.stop="deletePhoto(photo.id)">
              <text>删除</text>
            </view>
          </view>
        </view>
      </view>
    </view>

    <view v-if="photos.length === 0 && !isUploading" class="empty-state animate-fade-in-up" style="animation-delay: 0.3s;">
      <view class="empty-glass-icon float-breathing">
        <text class="empty-emoji">🖼️</text>
      </view>
      <text class="empty-text">图库空空如也</text>
      <text class="empty-hint">点击上方卡片，上传第一张珍贵影像吧</text>
    </view>

    <view style="height: 180rpx;"></view>

    <CustomTabBar :selected="1" />
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import CustomTabBar from '@/components/CustomTabBar.vue'
import { get, uploadFile, getToken, del } from '@/utils/request'

interface Photo {
  id: number
  filename: string
  url: string
  original_path: string
  created_at: string
}

const photos = ref<Photo[]>([])
const isUploading = ref(false)
const isSelectMode = ref(false)
const selectedPhotoIds = ref<number[]>([])

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

const loadPhotos = async () => {
  try {
    const data = await get<any[]>('/gallery/photos', { skip: 0, limit: 100 })
    photos.value = data.map(p => ({
      ...p,
      url: getFullUrl(p.original_path)
    }))
  } catch (error) {
    console.error('加载照片失败', error)
  }
}

const triggerUpload = () => {
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: async (res) => {
      const filePath = res.tempFilePaths[0]
      isUploading.value = true
      try {
        const newPhoto = await uploadFile({
          url: '/gallery/photos/upload',
          filePath,
          name: 'file'
        })
        photos.value = [{
          ...newPhoto,
          url: getFullUrl((newPhoto as any).original_path)
        }, ...photos.value]
        uni.showToast({ title: '上传成功', icon: 'success' })
      } catch (e: any) {
        uni.showToast({ title: '上传失败', icon: 'none' })
      } finally {
        isUploading.value = false
      }
    }
  })
}

const onPhotoTap = (photo: Photo) => {
  if (isSelectMode.value) {
    toggleSelect(photo.id)
  } else {
    uni.previewImage({
      current: photo.url,
      urls: photos.value.map(p => p.url)
    })
  }
}

const goToRepair = (photo: Photo) => {
  uni.navigateTo({
    url: `/pages/workshop/module?photoUrl=${encodeURIComponent(photo.url)}&photoId=${photo.id}`
  })
}

const deletePhoto = async (photoId: number) => {
  uni.showModal({
    title: '确认删除',
    content: '确定要删除这张照片吗？此操作不可恢复。',
    success: async (res) => {
      if (res.confirm) {
        try {
          await del(`/gallery/photos/${photoId}`)
          photos.value = photos.value.filter(p => p.id !== photoId)
          selectedPhotoIds.value = selectedPhotoIds.value.filter(id => id !== photoId)
          uni.showToast({ title: '删除成功', icon: 'success' })
        } catch (error) {
          uni.showToast({ title: '删除失败', icon: 'none' })
        }
      }
    }
  })
}

const enterSelectMode = () => { isSelectMode.value = true }
const exitSelectMode = () => { isSelectMode.value = false; selectedPhotoIds.value = [] }

const toggleSelect = (photoId: number) => {
  const index = selectedPhotoIds.value.indexOf(photoId)
  if (index === -1) {
    selectedPhotoIds.value.push(photoId)
  } else {
    selectedPhotoIds.value.splice(index, 1)
  }
}

const toggleSelectAll = () => {
  if (selectedPhotoIds.value.length === photos.value.length) {
    selectedPhotoIds.value = []
  } else {
    selectedPhotoIds.value = photos.value.map(p => p.id)
  }
}

const batchDelete = async () => {
  if (selectedPhotoIds.value.length === 0) return
  uni.showModal({
    title: '批量删除',
    content: `确定要删除选中的 ${selectedPhotoIds.value.length} 张照片吗？`,
    success: async (res) => {
      if (res.confirm) {
        try {
          for (const id of selectedPhotoIds.value) {
            await del(`/gallery/photos/${id}`)
          }
          photos.value = photos.value.filter(p => !selectedPhotoIds.value.includes(p.id))
          exitSelectMode()
          uni.showToast({ title: '删除成功', icon: 'success' })
        } catch (error) {
          uni.showToast({ title: '删除失败', icon: 'none' })
        }
      }
    }
  })
}

onMounted(() => {
  const token = getToken()
  if (!token) {
    uni.reLaunch({ url: '/pages/login/login' })
    return
  }
  loadPhotos()
})
</script>

<style lang="scss" scoped>
/* ================= 核心动画与环境氛围 ================= */
@keyframes fadeInUp {
  0% { opacity: 0; transform: translateY(40rpx) scale(0.98); }
  100% { opacity: 1; transform: translateY(0) scale(1); }
}

@keyframes floatBreathing {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10rpx); }
}

@keyframes orbDrift {
  0% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30rpx, -40rpx) scale(1.1); }
  66% { transform: translate(-20rpx, 30rpx) scale(0.9); }
  100% { transform: translate(0, 0) scale(1); }
}

.animate-fade-in-up {
  opacity: 0;
  animation: fadeInUp 0.7s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
}

.float-breathing { animation: floatBreathing 5s ease-in-out infinite; }

.float-hover {
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.3s ease;
  &:active {
    transform: scale(0.94);
    box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.05);
  }
}

/* 环境光晕 (氛围感核心) */
.ambient-background {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: var(--bg-elegant, #FAF8F5);
  z-index: -1; overflow: hidden;
}
.orb { position: absolute; border-radius: 50%; filter: blur(90px); opacity: 0.6; animation: orbDrift 15s ease-in-out infinite; }
.orb-gold { width: 600rpx; height: 600rpx; background: rgba(212, 175, 55, 0.25); top: -10%; left: -20%; }
.orb-champagne { width: 700rpx; height: 700rpx; background: rgba(242, 169, 127, 0.2); bottom: 20%; right: -20%; animation-delay: -5s; }
.orb-white { width: 500rpx; height: 500rpx; background: rgba(255, 255, 255, 0.8); top: 30%; left: 30%; filter: blur(60px); animation-delay: -10s; }

/* ================= 页面基础结构 ================= */
.gallery-page {
  min-height: 100vh;
  padding: 0 40rpx;
}

.page-header {
  padding: 40rpx 0 32rpx;
  .header-top { display: flex; justify-content: space-between; align-items: flex-start; }
  .page-title { display: block; font-size: 60rpx; font-weight: 800; color: var(--text-main, #3D352B); letter-spacing: 2rpx; }
  .page-subtitle { display: block; font-size: 26rpx; color: var(--text-muted, #A39B90); margin-top: 16rpx; font-weight: 500; }
}

/* 顶部选择按钮 (毛玻璃) */
.glass-btn {
  padding: 16rpx 40rpx; border-radius: 40rpx;
  background: rgba(255, 255, 255, 0.5); backdrop-filter: blur(16px);
  border: 1rpx solid rgba(255, 255, 255, 0.9);
  box-shadow: 0 8rpx 24rpx rgba(0,0,0,0.03), inset 0 2rpx 4rpx rgba(255,255,255,0.6);
  .action-text { font-size: 26rpx; color: var(--gold-dark, #B58D1F); font-weight: 800; }
}

/* ================= 批量操作栏 (高级悬浮胶囊) ================= */
.select-bar-wrapper { margin-bottom: 40rpx; }
.glass-panel {
  background: rgba(255, 255, 255, 0.6); backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px);
  border: 1rpx solid rgba(255, 255, 255, 0.8);
  box-shadow: 0 16rpx 40rpx rgba(44, 36, 23, 0.05), inset 0 4rpx 8rpx rgba(255, 255, 255, 0.5);
}
.select-bar {
  border-radius: 40rpx; padding: 24rpx 32rpx;
  .select-info {
    display: flex; justify-content: space-between; align-items: center; margin-bottom: 24rpx;
    .select-count { font-size: 30rpx; color: #5A4A32; font-weight: 800; }
    .select-all-btn {
      padding: 10rpx 28rpx; background: rgba(255, 255, 255, 0.8); border-radius: 30rpx;
      font-size: 24rpx; color: var(--gold-main); font-weight: 800; box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.02);
    }
  }
  .select-actions {
    display: flex; gap: 24rpx;
    .cancel-btn { flex: 1; padding: 20rpx 0; text-align: center; background: rgba(255,255,255,0.7); border-radius: 28rpx; font-size: 28rpx; color: #8C7A5A; font-weight: 700; border: 1px solid rgba(255,255,255,0.9); }
    .delete-btn { flex: 1; padding: 20rpx 0; text-align: center; background: linear-gradient(135deg, #FF7676, #EE5A24); border-radius: 28rpx; font-size: 28rpx; color: #fff; font-weight: 800; box-shadow: 0 8rpx 24rpx rgba(238, 90, 36, 0.2); }
  }
}

/* ================= 照片网格区域 ================= */
.photo-grid { display: flex; flex-wrap: wrap; gap: 24rpx; margin-bottom: 40rpx; }

/* 顶级毛玻璃上传卡片 */
.upload-card {
  box-sizing: border-box; width: calc(50% - 12rpx); aspect-ratio: 4/5;
  border-radius: 48rpx; /* 大圆角 */
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  position: relative; overflow: hidden;
  
  .upload-icon-wrap {
    width: 100rpx; height: 100rpx; border-radius: 50%;
    background: linear-gradient(135deg, var(--gold-main), var(--champagne-main));
    display: flex; align-items: center; justify-content: center; margin-bottom: 24rpx;
    box-shadow: 0 12rpx 32rpx rgba(212, 175, 55, 0.3), inset 0 4rpx 8rpx rgba(255,255,255,0.4);
    .upload-plus { font-size: 60rpx; color: #FFFFFF; font-weight: 300; margin-top: -4rpx; }
    .upload-loading { font-size: 40rpx; }
  }
  .upload-text { font-size: 32rpx; color: #5A4A32; font-weight: 800; margin-bottom: 8rpx; text-shadow: 0 2rpx 4rpx rgba(255,255,255,0.8); }
  .upload-hint { font-size: 22rpx; color: #A39B90; font-weight: 500; }
}

/* 独立照片卡片 */
.photo-card {
  box-sizing: border-box; width: calc(50% - 12rpx); aspect-ratio: 4/5;
  border-radius: 48rpx; overflow: hidden; position: relative;
  background: #FFFFFF; box-shadow: 0 12rpx 40rpx rgba(0,0,0,0.06);
  transform: translateZ(0); /* 开启硬件加速，让毛玻璃滑动更顺畅 */

  &.selected { box-shadow: 0 0 0 8rpx var(--gold-main); }
  .photo-img { width: 100%; height: 100%; display: block; }

  /* 悬浮选择框 (未选中时为毛玻璃) */
  .check-box {
    position: absolute; top: 24rpx; left: 24rpx; width: 48rpx; height: 48rpx; border-radius: 50%;
    background: rgba(255, 255, 255, 0.4); backdrop-filter: blur(8px);
    border: 2rpx solid rgba(255, 255, 255, 0.9);
    display: flex; align-items: center; justify-content: center; z-index: 10; transition: all 0.3s;
    box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.1);
    &.checked { background: var(--gold-main); border-color: var(--gold-main); transform: scale(1.1); }
    .check-mark { color: #FFF; font-size: 24rpx; font-weight: 800; }
  }

  /* 明亮毛玻璃沉浸式控制台 (参考音乐播放器) */
  .glass-overlay {
    position: absolute; bottom: 0; left: 0; right: 0;
    background: rgba(255, 255, 255, 0.3); /* 超透底色 */
    backdrop-filter: blur(24px) saturate(150%); -webkit-backdrop-filter: blur(24px) saturate(150%);
    border-top: 1rpx solid rgba(255, 255, 255, 0.5);
    padding: 24rpx; opacity: 0; transform: translateY(20rpx);
    transition: all 0.4s cubic-bezier(0.2, 0.8, 0.2, 1);
  }

  &:active .glass-overlay { opacity: 1; transform: translateY(0); }

  .photo-filename { 
    display: block; font-size: 24rpx; font-weight: 800; color: #2C2417; 
    margin-bottom: 20rpx; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    text-shadow: 0 2rpx 4rpx rgba(255,255,255,0.8);
  }
  
  .photo-actions { display: flex; gap: 16rpx; }
  .photo-action-btn {
    flex: 1; padding: 14rpx 0; text-align: center; border-radius: 20rpx; font-size: 22rpx; font-weight: 800;
    /* 胶囊按钮 */
    &.repair-btn { background: var(--gold-main); color: #FFF; box-shadow: 0 4rpx 12rpx rgba(212,175,55,0.4); }
    &.delete-action-btn { background: rgba(255,255,255,0.8); color: #FF7676; }
  }
}

/* ================= 空状态 ================= */
.empty-state {
  display: flex; flex-direction: column; align-items: center; padding: 160rpx 0;
  .empty-glass-icon {
    width: 160rpx; height: 160rpx; border-radius: 50%;
    background: rgba(255, 255, 255, 0.6); backdrop-filter: blur(20px);
    display: flex; align-items: center; justify-content: center; margin-bottom: 32rpx;
    border: 1px solid rgba(255, 255, 255, 0.9); box-shadow: 0 16rpx 40rpx rgba(0,0,0,0.03);
    .empty-emoji { font-size: 80rpx; filter: drop-shadow(0 8rpx 16rpx rgba(0,0,0,0.1)); }
  }
  .empty-text { font-size: 32rpx; font-weight: 800; color: #5A4A32; margin-bottom: 12rpx; }
  .empty-hint { font-size: 24rpx; color: #A39B90; font-weight: 500; }
}
</style>
<template>
  <Transition name="fade">
    <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center bg-[#2D2822]/30 backdrop-blur-sm p-4">
      <div class="bg-[#FDFBF7] rounded-2xl shadow-2xl max-w-md w-full overflow-hidden border border-[#DBCFB8]">
        <!-- 顶部雅致金装饰条 -->
        <div class="h-1.5 bg-gradient-to-r from-[#C9B598] via-[#A68966] to-[#C9B598]"></div>
        
        <div class="p-8">
          <!-- 标题区域 -->
          <div class="flex items-center mb-6">
            <div class="w-10 h-10 bg-[#F5F0E6] rounded-full flex items-center justify-center mr-4 border border-[#DBCFB8]">
              <svg class="w-5 h-5 text-[#A68966]" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
              </svg>
            </div>
            <h3 class="text-2xl font-serif font-medium text-[#8C7355] tracking-wide">{{ title }}</h3>
          </div>
          
          <!-- 内容区域 -->
          <div class="text-[#6B5D4A] leading-relaxed space-y-4">
            <p class="text-sm">尊敬的用户，欢迎使用《岁月笺影》！</p>
            
            <div class="bg-[#F5F0E6] border-l-2 border-[#A68966] p-4 rounded-r-lg">
              <p class="text-sm text-[#5C4D3A] font-medium">系统测试公告</p>
              <p class="text-xs text-[#6B5D4A]/80 mt-1">
                目前系统处于 <span class="font-semibold text-[#8C7355]">初步测试阶段</span>，部分高负载 AI 修复模块正在优化中。
              </p>
            </div>
            
            <div class="space-y-2 text-sm text-[#6B5D4A]">
              <p><span class="font-medium text-[#A68966]">当前开放模块：</span>拂尘 · 物理修复、真容 · 肖像精修、留音 · 声音复活。</p>
              <p><span class="font-medium text-[#A68966]">其他功能：</span>图库浏览、修复历史查询。</p>
              <p><span class="font-medium text-[#A68966]">功能跳转：</span>修复历史记录支持快速跳转至对应功能页。</p>
              <p><span class="font-medium text-[#A68966]">演示视频：</span>查看全功能演示。</p>
            </div>
            
            <div class="text-center pt-2">
              <a 
                href="https://pan.baidu.com/s/1We7qexhrvGqcwB15Uh2pOQ?pwd=q8xi" 
                target="_blank" 
                class="inline-block bg-[#E6DCC9] hover:bg-[#DBCFB8] text-[#5C4D3A] px-6 py-2 rounded-md text-sm font-medium transition-colors duration-300"
              >
                点击查看演示视频
              </a>
            </div>
          </div>
          
          <!-- 底部按钮 -->
          <div class="mt-8 flex justify-end">
            <button 
              @click="$emit('confirm')"
              class="bg-[#A68966] hover:bg-[#8C7355] text-white px-8 py-2 rounded-md font-medium transition-colors duration-300 focus:outline-none focus:ring-2 focus:ring-[#A68966] focus:ring-offset-2 focus:ring-offset-[#FDFBF7]"
            >
              {{ confirmText }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { watch, ref, onMounted } from 'vue'

interface Props {
  visible: boolean
  title?: string
  confirmText?: string
}

const props = withDefaults(defineProps<Props>(), {
  title: '系统部署说明',
  confirmText: '我知道了'
})

defineEmits(['confirm'])

// 公告消息内容
const announcementContent = `尊敬的用户，欢迎使用《岁月笺影》！

目前系统处于初步测试阶段，部分高负载 AI 修复模块正在优化中。

📋 当前开放模块：
• 拂尘 · 物理修复 - 智能去除照片划痕、污渍
• 真容 · 肖像精修 - 专业修复人物面部细节
• 留音 · 声音复活 - 让记忆中的声音穿越时空

📋 其他开放功能：
• 图库浏览
• 修复历史查询

💡 功能特色：
• 修复历史记录支持快速跳转至对应功能页
• 推荐使用测试账号体验完整功能

🎯 推荐测试账号：
账号：lihaha
密码：123456

💡 该账号已包含大量已修复照片，可直接体验完整功能，省去上传修复时间。

📹 演示视频：
点击查看全功能演示视频`

// 检查是否已经添加过公告消息
const hasAddedNotification = ref(false)

// 监听visible变化，当模态框显示时添加公告消息
watch(() => props.visible, (newVal) => {
  if (newVal && !hasAddedNotification.value) {
    addAnnouncementToNotificationCenter()
    hasAddedNotification.value = true
  }
})

// 添加公告到消息中心
const addAnnouncementToNotificationCenter = () => {
  // 延迟执行，确保NotificationCenter组件已挂载
  setTimeout(() => {
    const notificationCenter = document.querySelector('notification-center') as any
    if (notificationCenter && notificationCenter.addNotification) {
      notificationCenter.addNotification({
        type: 'announcement',
        title: '系统测试公告',
        message: '当前开放模块：拂尘 · 物理修复、真容 · 肖像精修、留音 · 声音复活',
        details: announcementContent
      })
    } else {
      // 备用方案：直接操作localStorage
      const existingNotifications = JSON.parse(localStorage.getItem('time_trace_notifications') || '[]')
      
      // 检查是否已经存在相同的公告
      const hasExistingAnnouncement = existingNotifications.some((n: any) => 
        n.type === 'announcement' && n.title === '系统测试公告'
      )
      
      if (!hasExistingAnnouncement) {
        const newNotification = {
          id: Date.now().toString(),
          type: 'announcement',
          title: '系统测试公告',
          message: '当前开放模块：拂尘 · 物理修复、真容 · 肖像精修、留音 · 声音复活',
          details: announcementContent,
          timestamp: new Date().toISOString(),
          read: false,
          showDetails: false
        }
        
        existingNotifications.unshift(newNotification)
        localStorage.setItem('time_trace_notifications', JSON.stringify(existingNotifications))
        
        // 触发自定义事件，通知消息中心更新
        window.dispatchEvent(new CustomEvent('notification-updated'))
      }
    }
  }, 100)
}

// 组件挂载时检查是否需要添加公告
onMounted(() => {
  // 检查是否已经显示过公告
  const hasSeenAnnouncement = localStorage.getItem('has_seen_announcement')
  if (!hasSeenAnnouncement && props.visible) {
    addAnnouncementToNotificationCenter()
    localStorage.setItem('has_seen_announcement', 'true')
  }
})
</script>

<style scoped>
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
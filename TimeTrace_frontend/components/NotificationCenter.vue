<template>
  <div class="relative">
    <!-- 消息图标按钮 -->
    <button 
      @click="toggleNotification"
      class="relative flex items-center gap-3 px-4 py-3 w-full text-sm text-gray-600 hover:bg-primary-50 hover:text-primary-700 rounded-xl transition-all duration-300 group"
    >
      <div class="w-9 h-9 rounded-full bg-gray-100 group-hover:bg-primary-200 group-hover:text-primary-800 flex items-center justify-center transition-colors relative">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0" />
        </svg>
        <!-- 未读消息小红点 -->
        <span 
          v-if="unreadCount > 0" 
          class="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center font-bold"
        >
          {{ unreadCount > 9 ? '9+' : unreadCount }}
        </span>
      </div>
      <div class="flex flex-col items-start">
        <span class="font-medium">消息</span>
        <span class="text-xs text-gray-400 group-hover:text-primary-500">
          {{ unreadCount > 0 ? `${unreadCount}条未读` : '暂无消息' }}
        </span>
      </div>
    </button>

    <!-- 消息弹出窗口 -->
    <div 
      v-if="isOpen" 
      class="absolute bottom-full left-0 mb-2 w-80 bg-white rounded-xl shadow-2xl border border-gray-100 z-50 animate-fade-in"
    >
      <!-- 窗口头部 -->
      <div class="p-4 border-b border-gray-100 bg-gradient-to-r from-primary-50 to-white">
        <div class="flex justify-between items-center">
          <h3 class="font-semibold text-gray-900">消息中心</h3>
          <div class="flex items-center gap-2">
            <button 
              @click="markAllAsRead" 
              class="text-xs text-primary-600 hover:text-primary-800 transition-colors"
              v-if="unreadCount > 0"
            >
              全部已读
            </button>
            <button 
              @click="clearAll" 
              class="text-xs text-gray-500 hover:text-red-600 transition-colors"
              v-if="notifications.length > 0"
            >
              清空
            </button>
          </div>
        </div>
      </div>

      <!-- 消息列表 -->
      <div class="max-h-96 overflow-y-auto custom-scrollbar">
        <!-- 空状态 -->
        <div 
          v-if="notifications.length === 0" 
          class="p-8 text-center text-gray-500"
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-12 h-12 mx-auto mb-3 text-gray-300">
            <path stroke-linecap="round" stroke-linejoin="round" d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0" />
          </svg>
          <p class="text-sm">暂无消息</p>
        </div>

        <!-- 消息项 -->
        <div 
          v-for="notification in notifications" 
          :key="notification.id"
          :class="[
            'p-4 border-b border-gray-50 cursor-pointer transition-colors hover:bg-gray-50',
            !notification.read ? 'bg-primary-25' : ''
          ]"
          @click="markAsRead(notification.id)"
        >
          <div class="flex items-start gap-3">
            <!-- 消息图标 -->
            <div :class="[
              'w-8 h-8 rounded-full flex items-center justify-center shrink-0',
              notification.type === 'success' ? 'bg-green-100 text-green-600' :
              notification.type === 'error' ? 'bg-red-100 text-red-600' :
              notification.type === 'warning' ? 'bg-yellow-100 text-yellow-600' :
              'bg-primary-100 text-primary-600'
            ]">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
                <path v-if="notification.type === 'success'" stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                <path v-else-if="notification.type === 'error'" stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                <path v-else-if="notification.type === 'warning'" stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                <path v-else stroke-linecap="round" stroke-linejoin="round" d="M12 18v-5.25m0 0a6.01 6.01 0 0 0 1.5-.189m-1.5.189a6.01 6.01 0 0 1-1.5-.189m3.75 7.478a12.06 12.06 0 0 1-4.5 0m3.75 2.383a14.406 14.406 0 0 1-3 0M14.25 18v-.192c0-.983.658-1.823 1.508-2.316a7.5 7.5 0 1 0-7.517 0c.85.493 1.509 1.333 1.509 2.316V18" />
              </svg>
            </div>
            
            <!-- 消息内容 -->
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium text-gray-900 mb-1">{{ notification.title }}</p>
              <p class="text-xs text-gray-600 leading-relaxed">{{ notification.message }}</p>
              <p class="text-xs text-gray-400 mt-2">{{ formatTime(notification.timestamp) }}</p>
            </div>
            
            <!-- 未读标记 -->
            <div v-if="!notification.read" class="w-2 h-2 bg-primary-500 rounded-full shrink-0 mt-2"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

interface Notification {
  id: string
  type: 'info' | 'success' | 'warning' | 'error'
  title: string
  message: string
  timestamp: Date
  read: boolean
  taskId?: string
  operationType?: string
}

const isOpen = ref(false)
const notifications = ref<Notification[]>([])

// 计算未读消息数量
const unreadCount = computed(() => {
  return notifications.value.filter(n => !n.read).length
})

// 切换消息窗口显示
const toggleNotification = () => {
  isOpen.value = !isOpen.value
}

// 标记单条消息为已读
const markAsRead = (id: string) => {
  const notification = notifications.value.find(n => n.id === id)
  if (notification) {
    notification.read = true
    saveToLocalStorage()
  }
}

// 标记所有消息为已读
const markAllAsRead = () => {
  notifications.value.forEach(n => n.read = true)
  saveToLocalStorage()
}

// 清空所有消息
const clearAll = () => {
  notifications.value = []
  saveToLocalStorage()
}

// 添加新消息
const addNotification = (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => {
  const newNotification: Notification = {
    id: Date.now().toString(),
    timestamp: new Date(),
    read: false,
    ...notification
  }
  
  notifications.value.unshift(newNotification)
  
  // 限制消息数量，最多保留50条
  if (notifications.value.length > 50) {
    notifications.value = notifications.value.slice(0, 50)
  }
  
  saveToLocalStorage()
}

// 格式化时间显示
const formatTime = (timestamp: Date) => {
  const now = new Date()
  const diff = now.getTime() - timestamp.getTime()
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  
  return timestamp.toLocaleDateString()
}

// 保存到本地存储
const saveToLocalStorage = () => {
  localStorage.setItem('time_trace_notifications', JSON.stringify(notifications.value))
}

// 从本地存储加载
const loadFromLocalStorage = () => {
  const stored = localStorage.getItem('time_trace_notifications')
  if (stored) {
    try {
      const parsed = JSON.parse(stored)
      // 转换时间戳为Date对象
      notifications.value = parsed.map((n: any) => ({
        ...n,
        timestamp: new Date(n.timestamp)
      }))
    } catch (error) {
      console.error('加载消息失败:', error)
    }
  }
}

// 点击外部关闭消息窗口
const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as HTMLElement
  if (!target.closest('.relative')) {
    isOpen.value = false
  }
}

onMounted(() => {
  loadFromLocalStorage()
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

// 暴露添加消息的方法给其他组件使用
defineExpose({
  addNotification
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 2px;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 2px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

.animate-fade-in {
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
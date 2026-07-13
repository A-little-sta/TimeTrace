<template>
  <div class="relative">
    <!-- 消息图标按钮 -->
    <button 
      @click="openModal"
      class="relative flex items-center gap-3 px-4 py-3 w-full text-sm text-gray-600 hover:bg-primary-50 hover:text-primary-700 rounded-xl transition-all duration-300 group"
    >
      <div class="w-9 h-9 rounded-full bg-gray-100 group-hover:bg-primary-200 group-hover:text-primary-800 flex items-center justify-center transition-colors relative">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0" />
        </svg>
        <!-- 未读消息小红点 -->
        <span 
          v-if="unreadCount > 0" 
          class="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center font-bold animate-pulse"
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

    <!-- 消息中心模态框 -->
    <Teleport to="body">
      <div 
        v-if="isModalOpen" 
        class="fixed inset-0 z-50 flex items-center justify-center p-4"
      >
        <!-- 背景遮罩 -->
        <div 
          class="absolute inset-0 bg-black/40 backdrop-blur-sm transition-opacity duration-300"
          @click="closeModal"
        ></div>
        
        <!-- 模态框内容 -->
        <div 
          class="relative w-full max-w-2xl max-h-[85vh] bg-white rounded-2xl shadow-2xl border border-gray-100 overflow-hidden animate-modal-in"
        >
          <!-- 头部 -->
          <div class="sticky top-0 z-10 p-6 border-b border-gray-100 bg-gradient-to-r from-primary-50 to-white">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0" />
                  </svg>
                </div>
                <div>
                  <h2 class="text-xl font-semibold text-gray-900">消息中心</h2>
                  <p class="text-sm text-gray-500">{{ notifications.length }} 条消息</p>
                </div>
              </div>
              <div class="flex items-center gap-3">
                <button 
                  @click="markAllAsRead" 
                  class="px-4 py-2 text-sm text-primary-600 hover:text-primary-800 hover:bg-primary-50 rounded-lg transition-colors"
                  v-if="unreadCount > 0"
                >
                  全部已读
                </button>
                <button 
                  @click="clearAll" 
                  class="px-4 py-2 text-sm text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                  v-if="notifications.length > 0"
                >
                  清空
                </button>
                <button 
                  @click="closeModal" 
                  class="w-10 h-10 flex items-center justify-center text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
          </div>

          <!-- 消息列表 -->
          <div class="max-h-[calc(85vh-120px)] overflow-y-auto custom-scrollbar">
            <!-- 空状态 -->
            <div 
              v-if="notifications.length === 0" 
              class="p-16 text-center"
            >
              <div class="w-20 h-20 mx-auto mb-6 rounded-full bg-gray-100 flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-10 h-10 text-gray-400">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0" />
                </svg>
              </div>
              <h3 class="text-lg font-medium text-gray-900 mb-2">暂无消息</h3>
              <p class="text-sm text-gray-500">您还没有收到任何消息</p>
            </div>

            <!-- 消息项 -->
            <div 
              v-for="notification in notifications" 
              :key="notification.id"
              :class="[
                'p-5 border-b border-gray-50 cursor-pointer transition-all duration-200',
                !notification.read ? 'bg-primary-25 hover:bg-primary-50' : 'hover:bg-gray-50'
              ]"
              @click="handleNotificationClick(notification)"
            >
              <div class="flex items-start gap-4">
                <!-- 消息图标 -->
                <div :class="[
                  'w-12 h-12 rounded-xl flex items-center justify-center shrink-0',
                  notification.type === 'success' ? 'bg-green-100 text-green-600' :
                  notification.type === 'error' ? 'bg-red-100 text-red-600' :
                  notification.type === 'warning' ? 'bg-yellow-100 text-yellow-600' :
                  notification.type === 'announcement' ? 'bg-amber-100 text-amber-600' :
                  'bg-primary-100 text-primary-600'
                ]">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
                    <path v-if="notification.type === 'success'" stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                    <path v-else-if="notification.type === 'error'" stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                    <path v-else-if="notification.type === 'warning'" stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                    <path v-else-if="notification.type === 'announcement'" stroke-linecap="round" stroke-linejoin="round" d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0" />
                    <path v-else stroke-linecap="round" stroke-linejoin="round" d="M12 18v-5.25m0 0a6.01 6.01 0 0 0 1.5-.189m-1.5.189a6.01 6.01 0 0 1-1.5-.189m3.75 7.478a12.06 12.06 0 0 1-4.5 0m3.75 2.383a14.406 14.406 0 0 1-3 0M14.25 18v-.192c0-.983.658-1.823 1.508-2.316a7.5 7.5 0 1 0-7.517 0c.85.493 1.509 1.333 1.509 2.316V18" />
                  </svg>
                </div>
                
                <!-- 消息内容 -->
                <div class="flex-1 min-w-0">
                  <div class="flex items-center justify-between mb-2">
                    <h3 class="text-base font-semibold text-gray-900">{{ notification.title }}</h3>
                    <span class="text-sm text-gray-400">{{ formatTime(notification.timestamp) }}</span>
                  </div>
                  <p class="text-sm text-gray-600 leading-relaxed mb-3">{{ notification.message }}</p>
                  
                  <!-- 公告详情内容 -->
                  <div 
                    v-if="notification.type === 'announcement' && notification.details"
                    class="mb-3"
                  >
                    <button 
                      @click.stop="toggleNotificationDetails(notification.id)"
                      class="text-sm text-amber-600 hover:text-amber-800 transition-colors mb-3 flex items-center gap-1"
                    >
                      {{ notification.showDetails ? '收起详情' : '查看详情' }}
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" :class="['w-4 h-4 transition-transform duration-300', notification.showDetails ? 'rotate-180' : '']">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                      </svg>
                    </button>
                    <div 
                      v-if="notification.showDetails"
                      class="p-4 bg-amber-50 border border-amber-200 rounded-xl"
                    >
                      <div class="text-sm text-amber-800 leading-relaxed whitespace-pre-wrap">{{ notification.details }}</div>
                    </div>
                  </div>
                  
                  <!-- 操作按钮 -->
                  <div v-if="notification.action" class="flex gap-3">
                    <button 
                      @click.stop="handleNotificationAction(notification)"
                      :class="[
                        'px-4 py-2 text-sm rounded-lg font-medium transition-all duration-200',
                        notification.type === 'success' ? 'bg-green-100 text-green-700 hover:bg-green-200' :
                        notification.type === 'error' ? 'bg-red-100 text-red-700 hover:bg-red-200' :
                        notification.type === 'warning' ? 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200' :
                        'bg-primary-100 text-primary-700 hover:bg-primary-200'
                      ]"
                    >
                      {{ notification.action.label }}
                    </button>
                  </div>
                </div>
                
                <!-- 未读标记 -->
                <div v-if="!notification.read" class="w-3 h-3 bg-primary-500 rounded-full shrink-0 mt-3"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

interface Notification {
  id: string
  type: 'info' | 'success' | 'warning' | 'error' | 'announcement'
  title: string
  message: string
  timestamp: Date
  read: boolean
  taskId?: string
  operationType?: string
  details?: string // 详细内容，用于公告类型
  showDetails?: boolean // 是否显示详情
  action?: {
    type: 'navigate'
    route: string
    label: string
  } // 操作按钮，如跳转到创作时光轴
}

const isModalOpen = ref(false)
const notifications = ref<Notification[]>([])

// 计算未读消息数量
const unreadCount = computed(() => {
  return notifications.value.filter(n => !n.read).length
})

// 打开模态框
const openModal = () => {
  isModalOpen.value = true
  document.body.style.overflow = 'hidden'
}

// 关闭模态框
const closeModal = () => {
  isModalOpen.value = false
  document.body.style.overflow = ''
}

// 处理通知点击
const handleNotificationClick = (notification: Notification) => {
  // 标记为已读
  if (!notification.read) {
    notification.read = true
    saveToLocalStorage()
  }
}

// 处理通知操作
const handleNotificationAction = (notification: Notification) => {
  if (notification.action?.type === 'navigate') {
    // 使用Vue Router跳转到指定路由
    router.push(notification.action.route)
    // 标记为已读
    if (!notification.read) {
      notification.read = true
      saveToLocalStorage()
    }
    // 关闭模态框
    closeModal()
  }
}

// 切换消息详情显示
const toggleNotificationDetails = (id: string) => {
  const notification = notifications.value.find(n => n.id === id)
  if (notification) {
    // 如果是公告类型，切换详情显示
    if (notification.type === 'announcement') {
      notification.showDetails = !notification.showDetails
    }
    // 标记为已读
    if (!notification.read) {
      notification.read = true
    }
    saveToLocalStorage()
  }
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
        timestamp: new Date(n.timestamp),
        showDetails: n.showDetails || false
      }))
    } catch (error) {
      console.error('加载消息失败:', error)
    }
  }
}

// 监听通知更新事件
const handleNotificationUpdate = () => {
  loadFromLocalStorage()
}

// 监听全局添加消息事件
const handleAddNotificationEvent = (event: CustomEvent) => {
  if (event.detail) {
    addNotification(event.detail)
    // 收到新消息时，可以添加小红点跳动或提示音效果
    if (event.detail.type === 'success' || event.detail.type === 'error') {
      // 可以在这里添加声音提示
      console.log('收到重要通知:', event.detail.title)
    }
  }
}

// 键盘事件处理：按ESC键关闭模态框
const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Escape' && isModalOpen.value) {
    closeModal()
  }
}

onMounted(() => {
  loadFromLocalStorage()
  window.addEventListener('keydown', handleKeydown)
  window.addEventListener('notification-updated', handleNotificationUpdate)
  // 监听全局添加消息事件
  window.addEventListener('add-notification', handleAddNotificationEvent as EventListener)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
  window.removeEventListener('notification-updated', handleNotificationUpdate)
  // 移除监听
  window.removeEventListener('add-notification', handleAddNotificationEvent as EventListener)
})

// 暴露添加消息的方法给其他组件使用
defineExpose({
  addNotification
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 3px;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* 模态框进入动画 */
.animate-modal-in {
  animation: modalIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes modalIn {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(-20px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

/* 背景遮罩动画 */
.bg-black\/40 {
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
</style>
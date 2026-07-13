<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { api } from './services/api'

// 任务状态监听
const taskPollingInterval = ref<number | null>(null)
const lastTaskStatus = ref<any[]>([])

// 定义模块名映射
const moduleNameMap: Record<string, string> = {
  'dustless': '拂尘 · 物理修复',
  'time_engine': '时光引擎',
  'qingying': '清影 · 画质重构',
  'colorize': '流光 · 色彩复苏',
  'trueface': '真容 · 肖像精修',
  'voice': '留音 · 语音魔法',
  'liveportrait': '灵动 · 人像复活'
}

// 当检测到新任务开始
const onTaskStart = (task: any) => {
  const moduleName = moduleNameMap[task.task_type] || '影像修复'
  
  // 触发全局事件，让 NotificationCenter 捕获
  window.dispatchEvent(new CustomEvent('add-notification', {
    detail: {
      type: 'info',
      title: '任务开始',
      message: `您的【${moduleName}】任务已开始处理，请稍候...`,
      taskId: task.id
    }
  }))
}

// 当检测到任务完成
const onTaskComplete = (task: any) => {
  const moduleName = moduleNameMap[task.task_type] || '影像修复'
  
  window.dispatchEvent(new CustomEvent('add-notification', {
    detail: {
      type: 'success',
      title: '修复完成',
      message: `您的【${moduleName}】任务已处理完成！点击查看对比效果。`,
      taskId: task.id
    }
  }))
}

// 当任务失败
const onTaskError = (task: any) => {
  const moduleName = moduleNameMap[task.task_type] || '影像修复'
  
  window.dispatchEvent(new CustomEvent('add-notification', {
    detail: {
      type: 'error',
      title: '处理异常',
      message: `抱歉，您的【${moduleName}】修复任务遇到问题：${task.error_message || '未知错误'}`
    }
  }))
}

// 检查是否有正在进行的任务
const checkActiveTasks = async () => {
  try {
    // 首先检查本地存储中是否有正在进行的任务
    const storedTasks = localStorage.getItem('time_trace_processing_tasks')
    if (!storedTasks) {
      return false // 没有任务，不需要轮询
    }
    
    const tasks = JSON.parse(storedTasks)
    if (tasks.length === 0) {
      return false // 没有任务，不需要轮询
    }
    
    // 如果有正在进行的任务，才进行API请求
    const activeTasks = await api.getActiveTasks()
    
    // 检查状态变化
    activeTasks.forEach((task: any) => {
      const lastTask = lastTaskStatus.value.find(t => t.id === task.id)
      
      if (!lastTask) {
        // 新任务开始
        if (task.status === 'processing') {
          onTaskStart(task)
        }
      } else {
        // 状态变化
        if (lastTask.status === 'processing' && task.status === 'completed') {
          onTaskComplete(task)
        } else if (lastTask.status === 'processing' && task.status === 'failed') {
          onTaskError(task)
        }
      }
    })
    
    // 更新最后状态
    lastTaskStatus.value = activeTasks
    
    return activeTasks.length > 0
    
  } catch (error) {
    console.error('检查任务状态失败:', error)
    return false
  }
}

// 轮询检查任务状态
const startTaskPolling = async () => {
  if (taskPollingInterval.value) return
  
  // 先检查一次是否有任务需要轮询
  const hasActiveTasks = await checkActiveTasks()
  if (!hasActiveTasks) {
    console.log('没有正在进行的任务，停止轮询')
    return
  }
  
  taskPollingInterval.value = window.setInterval(async () => {
    const hasActiveTasks = await checkActiveTasks()
    if (!hasActiveTasks) {
      // 没有任务了，停止轮询
      stopTaskPolling()
    }
  }, 10000) // 每10秒检查一次，减少请求频率
}

// 停止轮询
const stopTaskPolling = () => {
  if (taskPollingInterval.value) {
    clearInterval(taskPollingInterval.value)
    taskPollingInterval.value = null
    console.log('任务状态轮询已停止')
  }
}

// 监听任务开始事件
const handleTaskStart = (event: CustomEvent) => {
  console.log('监听到任务开始事件，启动轮询')
  startTaskPolling()
}

onMounted(() => {
  // 监听任务开始事件，而不是立即启动轮询
  window.addEventListener('time_trace_task_start', handleTaskStart as EventListener)
  
  // 检查一次是否有遗留的正在进行的任务
  startTaskPolling()
})

onUnmounted(() => {
  // 停止任务状态轮询
  stopTaskPolling()
  // 移除事件监听
  window.removeEventListener('time_trace_task_start', handleTaskStart as EventListener)
})
</script>

<template>
  <router-view></router-view>
</template>

<style>
/* Global styles if needed */
</style>
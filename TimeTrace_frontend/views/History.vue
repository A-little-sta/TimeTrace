<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { api } from '../services/api';
import { History } from '../types';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../store';
import ImageCompare from '../components/ImageCompare.vue';

const histories = ref<History[]>([]);
const selectedHistory = ref<History | null>(null);
const isLoading = ref(false);
const router = useRouter();
const authStore = useAuthStore();

// 正在修复中的任务
const processingTasks = ref<Array<{
  id: string;
  operation_type: string;
  task_id: string;
  start_time: Date;
  status: 'processing' | 'completed' | 'failed';
}>>([]);

// 检查是否有正在进行的任务
const checkProcessingTasks = () => {
  const storedTasks = localStorage.getItem('time_trace_processing_tasks');
  if (storedTasks) {
    try {
      const tasks = JSON.parse(storedTasks);
      processingTasks.value = tasks.map((task: any) => ({
        ...task,
        start_time: new Date(task.start_time)
      }));
    } catch (error) {
      console.error('加载正在进行的任务失败:', error);
    }
  }
};

// 更新任务状态
const updateTaskStatus = (taskId: string, status: 'processing' | 'completed' | 'failed') => {
  const taskIndex = processingTasks.value.findIndex(task => task.task_id === taskId);
  if (taskIndex !== -1) {
    processingTasks.value[taskIndex].status = status;
    
    // 保存到本地存储
    localStorage.setItem('time_trace_processing_tasks', JSON.stringify(processingTasks.value));
    
    // 如果任务完成或失败，从列表中移除（保留一段时间供查看）
    if (status === 'completed' || status === 'failed') {
      setTimeout(() => {
        processingTasks.value = processingTasks.value.filter(task => task.task_id !== taskId);
        localStorage.setItem('time_trace_processing_tasks', JSON.stringify(processingTasks.value));
      }, 5000); // 5秒后移除
    }
  }
};

// 添加新任务
const addProcessingTask = (taskData: {
  id: string;
  operation_type: string;
  task_id: string;
}) => {
  const newTask = {
    ...taskData,
    start_time: new Date(),
    status: 'processing' as const
  };
  
  processingTasks.value.push(newTask);
  localStorage.setItem('time_trace_processing_tasks', JSON.stringify(processingTasks.value));
  
  // 创建任务开始的消息通知
  sendNotification({
    type: 'info',
    title: `${getOperationName(taskData.operation_type)}开始`,
    message: `您的${getOperationName(taskData.operation_type)}任务已开始处理，请稍候...`,
    taskId: taskData.task_id,
    operationType: taskData.operation_type
  });
};

// 轮询检查任务状态
let pollingInterval: number | null = null;

const startTaskPolling = () => {
  if (pollingInterval) return;
  
  pollingInterval = window.setInterval(async () => {
    if (processingTasks.value.length === 0) return;
    
    for (const task of processingTasks.value) {
      if (task.status === 'processing') {
        try {
          const taskStatus = await api.getTaskStatus(task.task_id);
          
          if (taskStatus.status === 'completed') {
            updateTaskStatus(task.task_id, 'completed');
            
            // 发送完成通知
            sendNotification({
              type: 'success',
              title: `${getOperationName(task.operation_type)}完成`,
              message: `您的${getOperationName(task.operation_type)}任务已完成，可以查看结果了。`,
              taskId: task.task_id,
              operationType: task.operation_type
            });
            
            // 重新加载历史记录
            loadHistories();
            
          } else if (taskStatus.status === 'failed') {
            updateTaskStatus(task.task_id, 'failed');
            
            // 发送失败通知
            sendNotification({
              type: 'error',
              title: `${getOperationName(task.operation_type)}失败`,
              message: `抱歉，您的${getOperationName(task.operation_type)}任务处理失败，请重试。`,
              taskId: task.task_id,
              operationType: task.operation_type
            });
          }
        } catch (error) {
          console.error('检查任务状态失败:', error);
        }
      }
    }
  }, 3000); // 每3秒检查一次
};

// 停止轮询
const stopTaskPolling = () => {
  if (pollingInterval) {
    clearInterval(pollingInterval);
    pollingInterval = null;
  }
};

// 发送通知
const sendNotification = (notification: {
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  taskId?: string;
  operationType?: string;
}) => {
  // 通过事件总线发送通知
  window.dispatchEvent(new CustomEvent('time_trace_notification', {
    detail: notification
  }));
};

// 音频播放器状态
const audioError = ref<string>('');
const audioReady = ref<boolean>(false);
const audioLoading = ref<boolean>(false);
const audioStalled = ref<boolean>(false);

// 音频播放器错误处理
const handleAudioError = (event: Event) => {
  const audio = event.target as HTMLAudioElement;
  console.error('音频播放错误:', audio.error);
  
  switch (audio.error?.code) {
    case audio.error.MEDIA_ERR_ABORTED:
      audioError.value = '音频加载被中止';
      break;
    case audio.error.MEDIA_ERR_NETWORK:
      audioError.value = '网络错误，音频文件无法加载';
      break;
    case audio.error.MEDIA_ERR_DECODE:
      audioError.value = '音频格式不支持或文件损坏';
      break;
    case audio.error.MEDIA_ERR_SRC_NOT_SUPPORTED:
      audioError.value = '音频格式不支持';
      break;
    default:
      audioError.value = '未知音频播放错误';
  }
  
  // 尝试直接下载音频文件
  setTimeout(() => {
    if (selectedHistory.value?.result_url) {
      const link = document.createElement('a');
      link.href = selectedHistory.value.result_url;
      link.download = 'audio_file.wav';
      link.style.display = 'none';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  }, 1000);
};

// 音频开始加载时的处理
const handleAudioLoadStart = () => {
  audioLoading.value = true;
  audioStalled.value = false;
  console.log('音频开始加载');
};

// 音频可以播放时的处理
const handleAudioCanPlay = () => {
  audioReady.value = true;
  audioLoading.value = false;
  audioStalled.value = false;
  audioError.value = '';
  console.log('音频可以播放');
};

// 音频加载缓慢时的处理
const handleAudioStalled = () => {
  audioStalled.value = true;
  console.log('音频加载缓慢');
};

// 下载音频文件
const downloadAudioFile = () => {
  if (!selectedHistory.value?.result_url) {
    alert('无法下载，音频文件不存在');
    return;
  }
  
  try {
    const link = document.createElement('a');
    link.href = selectedHistory.value.result_url;
    link.download = 'audio_file.wav';
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    console.log('音频文件下载成功');
  } catch (error) {
    console.error('下载音频文件失败:', error);
    alert('下载失败，请稍后重试');
  }
};

// 下载视频文件
const downloadVideoFile = () => {
  if (!selectedHistory.value?.result_url) {
    alert('无法下载，视频文件不存在');
    return;
  }
  
  try {
    const link = document.createElement('a');
    link.href = selectedHistory.value.result_url;
    link.download = 'video_file.mp4';
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    console.log('视频文件下载成功');
  } catch (error) {
    console.error('下载视频文件失败:', error);
    alert('下载失败，请稍后重试');
  }
};

// 当选择新的历史记录时重置音频状态
const resetAudioState = () => {
  audioError.value = '';
  audioReady.value = false;
  audioLoading.value = false;
  audioStalled.value = false;
};

// 操作类型中文映射
const operationTypeMap: Record<string, string> = {
  'dustless': '拂尘修复',
  'colorize': '流光上色',
  'clarity': '清影清晰',
  'trueface': '真容修复',
  'tts': '文本转语音',
  'voice_clone': '留音',
  'voice': '留音',                 // 新增
  'live_portrait': '灵动',
  'liveportrait': '灵动',          // 新增
  'liveportrait_video': '灵动',     // 新增
  'time_engine': '时光引擎'        // 新增
};

// 操作类型到模块ID的映射
const operationToModuleMap: Record<string, string> = {
  'dustless': 'dustless',
  'colorize': 'liuguang',
  'clarity': 'qingying',
  'trueface': 'zhenrong',
  'tts': 'voice',
  'voice_clone': 'voice',
  'voice': 'voice',
  'live_portrait': 'live_portrait',
  'liveportrait': 'live_portrait',
  'liveportrait_video': 'live_portrait',
  'time_engine': 'time_engine'
};

// 获取历史记录对应的模块ID
const getModuleIdFromHistory = (history: History): string => {
  return operationToModuleMap[history.operation_type] || 'dustless';
};

// 跳转到对应模块的修复工坊
const navigateToModule = (history: History) => {
  const moduleId = getModuleIdFromHistory(history);
  router.push(`/workshop/${moduleId}?history_id=${history.id}`);
};

// 媒体类型中文映射
const mediaTypeMap: Record<string, string> = {
  'image': '图片',
  'audio': '音频',
  'video': '视频'
};

const loadHistories = async () => {
  isLoading.value = true;
  try {
    const data = await api.getHistories();
    histories.value = data;
    
    // 检查是否有正在进行的任务
    checkProcessingTasks();
    
    // 如果有正在进行的任务，开始轮询
    if (processingTasks.value.length > 0) {
      startTaskPolling();
    }
  } catch (error) {
    console.error("Failed to load histories", error);
  } finally {
    isLoading.value = false;
  }
};

// 清空所有历史记录
const clearAllHistories = async () => {
  if (histories.value.length === 0) {
    alert('当前没有历史记录可清空');
    return;
  }

  if (!confirm(`确定要清空所有 ${histories.value.length} 条创作记录吗？\n\n此操作无法撤销，所有记录将被永久删除。`)) {
    return;
  }

  try {
    const result = await api.clearAllHistories();
    alert(result.message);
    
    // 清空本地列表
    histories.value = [];
    selectedHistory.value = null;
    
    console.log('所有历史记录已清空');
  } catch (error) {
    console.error('清空历史记录失败:', error);
    alert('清空失败，请稍后重试');
  }
};

const selectHistory = (history: History) => {
  console.log('选择的历史记录:', history);
  console.log('原图路径:', history.original_path, '原图URL:', history.original_url);
  console.log('结果路径:', history.result_path, '结果URL:', history.result_url);
  
  // 重置音频状态
  resetAudioState();
  
  selectedHistory.value = history;
};

const closeDetail = () => {
  selectedHistory.value = null;
};

// 确认删除历史记录（从列表）
const confirmDeleteHistory = (history: History) => {
  if (confirm(`确定要删除这条"${getOperationName(history.operation_type)}"的修复记录吗？\n\n此操作无法撤销。`)) {
    deleteHistoryById(history.id);
  }
};

// 删除历史记录（从详情）
const deleteHistory = () => {
  if (selectedHistory.value && confirm(`确定要删除这条"${getOperationName(selectedHistory.value.operation_type)}"的修复记录吗？\n\n此操作无法撤销。`)) {
    deleteHistoryById(selectedHistory.value.id);
  }
};

// 执行删除操作
const deleteHistoryById = async (historyId: number) => {
  try {
    await api.deleteHistory(historyId);
    
    // 从列表中移除已删除的记录
    histories.value = histories.value.filter(h => h.id !== historyId);
    
    // 如果当前查看的详情是被删除的记录，关闭详情模态框
    if (selectedHistory.value?.id === historyId) {
      selectedHistory.value = null;
    }
    
    alert('删除成功！');
  } catch (error) {
    console.error('删除历史记录失败:', error);
    alert('删除失败，请稍后重试');
  }
};

const getOperationName = (type: string): string => {
  return operationTypeMap[type] || type;
};

const formatDate = (dateString: string): string => {
  try {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (e) {
    return dateString;
  }
};

// 下载结果文件 - 采用 Blob 转换方案，强制触发浏览器下载对话框
const downloadHistoryResult = async () => {
  if (!selectedHistory.value?.result_url) {
    alert('无法下载，结果文件不存在');
    return;
  }
  
  try {
    // 1. 使用 fetch 获取图片的原始数据
    const response = await fetch(selectedHistory.value.result_url);
    if (!response.ok) throw new Error('网络响应错误');
    
    // 2. 将数据转换为 Blob
    const blob = await response.blob();
    
    // 3. 创建一个指向该 Blob 的本地 URL
    const blobUrl = window.URL.createObjectURL(blob);
    
    // 4. 生成文件名
    const timestamp = new Date(selectedHistory.value.created_at).getTime();
    const operationName = getOperationName(selectedHistory.value.operation_type);
    
    let fileExtension = '.jpg';
    if (selectedHistory.value.media_type === 'audio') {
      fileExtension = '.wav';
    } else if (selectedHistory.value.media_type === 'video') {
      fileExtension = '.mp4';
    } else if (blob.type.includes('png')) {
      fileExtension = '.png';
    }
    
    const filename = `${operationName}_${timestamp}${fileExtension}`;
    
    // 5. 创建下载链接并触发下载
    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = filename;
    link.style.display = 'none';
    
    document.body.appendChild(link);
    link.click();
    
    // 延迟清理，确保点击事件完成
    setTimeout(() => {
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);
    }, 100);
    
    console.log("尝试触发下载，如未弹出保存对话框，请在新页面右键另存为");
    
  } catch (fallbackError) {
    console.error('降级方案也失败:', fallbackError);
    
    // 方案C：最终降级 - 直接打开图片
    window.open(selectedHistory.value.result_url, '_blank');
    alert('下载失败，图片已在新标签页打开，请右键选择"图片另存为..."进行保存。');
  }
};

onMounted(() => {
  // Check if user is authenticated
  if (!authStore.isAuthenticated) {
    router.push('/login');
    return;
  }
  
  loadHistories();
  
  // 监听任务开始事件
  window.addEventListener('time_trace_task_start', handleTaskStart);
  
  // 监听通知事件
  window.addEventListener('time_trace_notification', handleNotification);
});

onUnmounted(() => {
  stopTaskPolling();
  window.removeEventListener('time_trace_task_start', handleTaskStart);
  window.removeEventListener('time_trace_notification', handleNotification);
});

// 处理任务开始事件
const handleTaskStart = (event: CustomEvent) => {
  const { taskData } = event.detail;
  addProcessingTask(taskData);
  startTaskPolling();
};

// 处理通知事件
const handleNotification = (event: CustomEvent) => {
  // 这里可以处理接收到的通知
  console.log('收到通知:', event.detail);
};
</script>

<template>
  <div class="p-8 md:p-12 max-w-7xl mx-auto min-h-full flex flex-col animate-fade-in bg-gradient-to-br from-gray-50 to-white">
    <!-- Header -->
    <div class="mb-12">
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 class="text-4xl font-serif-title font-bold text-gray-900 tracking-tight mb-3">创作时光轴</h1>
          <p class="text-gray-500 font-light text-lg">记录您所有的修复与创作历程</p>
        </div>
        
        <!-- 清空按钮 -->
        <button 
          v-if="histories.length > 0"
          @click="clearAllHistories"
          class="px-6 py-2 bg-red-500 hover:bg-red-600 text-white rounded-xl text-sm font-medium transition-colors shadow-md hover:shadow-lg flex items-center gap-2"
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
            <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
          </svg>
          清空所有记录
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="flex justify-center items-center py-20">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
    </div>

    <!-- Empty State -->
    <div v-else-if="histories.length === 0" class="flex flex-col items-center justify-center py-20">
      <div class="w-24 h-24 mb-6 text-gray-300">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>
      <h2 class="text-xl font-serif-title font-medium text-gray-900 mb-2">时光轴空空如也</h2>
      <p class="text-gray-500 text-center max-w-md">您还没有创作记录，快去体验我们的修复与生成功能吧！</p>
      <button 
        @click="router.push('/workshop')" 
        class="mt-6 px-6 py-3 bg-primary-500 hover:bg-primary-600 text-white rounded-xl text-sm font-medium transition-colors shadow-md hover:shadow-lg"
      >
        开始创作
      </button>
    </div>

    <!-- 正在修复中的任务 -->
    <div v-if="processingTasks.length > 0" class="mb-8">
      <h3 class="text-xl font-serif-title font-medium text-gray-900 mb-4">正在修复中</h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
        <div 
          v-for="task in processingTasks" 
          :key="task.id" 
          class="group relative aspect-[3/4] rounded-3xl overflow-hidden bg-gradient-to-br from-blue-50 to-blue-100 border-2 border-dashed border-blue-200 flex flex-col items-center justify-center p-6 animate-pulse"
        >
          <!-- 加载动画 -->
          <div class="w-16 h-16 mb-4 text-blue-500 relative">
            <div class="absolute inset-0 border-4 border-blue-200 rounded-full"></div>
            <div class="absolute inset-2 border-4 border-blue-400 rounded-full animate-spin"></div>
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-8 h-8 absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          
          <h3 class="text-lg font-medium text-gray-900 text-center mb-2">{{ getOperationName(task.operation_type) }}</h3>
          <p class="text-gray-600 text-sm text-center">正在修复中...</p>
          <p class="text-xs text-gray-500 text-center mt-2">{{ formatTime(task.start_time) }}</p>
          
          <!-- 状态指示器 -->
          <div class="absolute top-4 right-4">
            <div class="w-3 h-3 rounded-full" :class="{
              'bg-blue-500 animate-pulse': task.status === 'processing',
              'bg-green-500': task.status === 'completed',
              'bg-red-500': task.status === 'failed'
            }"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- History Grid -->
    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
      <div 
        v-for="(history, index) in histories" 
        :key="history.id" 
        class="group relative aspect-[3/4] rounded-3xl overflow-hidden bg-white shadow-sm hover:shadow-[0_20px_40px_-15px_rgba(207,176,123,0.3)] hover:-translate-y-2 transition-all duration-500 animate-fade-in cursor-pointer"
        :style="{ animationDelay: `${index * 50}ms` }"
        @click="selectHistory(history)"
      >
        <!-- 音频历史记录 -->
        <div v-if="history.media_type === 'audio' || history.result_url?.endsWith('.wav') || history.result_url?.endsWith('.mp3') || history.operation_type === 'voice' || history.operation_type === 'voice_clone' || history.operation_type === 'tts'" class="w-full h-full bg-gradient-to-br from-primary-50 to-primary-100 flex flex-col items-center justify-center p-6">
          <div class="w-16 h-16 mb-4 text-primary-500">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19.114 5.636a9 9 0 010 12.728M16.463 8.288a5.25 5.25 0 010 7.424M6.75 8.25l4.72-4.72a.75.75 0 011.28.53v15.88a.75.75 0 01-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.01 9.01 0 012.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75z" />
            </svg>
          </div>
          <h3 class="text-lg font-medium text-gray-900 text-center mb-2">{{ getOperationName(history.operation_type) }}</h3>
          <p class="text-gray-600 text-sm text-center">{{ mediaTypeMap[history.media_type] }}</p>
        </div>
        
        <!-- 视频历史记录 -->
        <div v-else-if="history.media_type === 'video' || history.result_url?.endsWith('.mp4') || history.result_url?.endsWith('.webm') || history.operation_type === 'live_portrait' || history.operation_type === 'liveportrait' || history.operation_type === 'liveportrait_video'" class="w-full h-full bg-gradient-to-br from-blue-50 to-blue-100 flex flex-col items-center justify-center p-6 relative">
          <div class="w-16 h-16 mb-4 text-blue-500">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25h-9A2.25 2.25 0 002.25 7.5v9a2.25 2.25 0 002.25 2.25z" />
            </svg>
          </div>
          <h3 class="text-lg font-medium text-gray-900 text-center mb-2">{{ getOperationName(history.operation_type) }}</h3>
          <p class="text-gray-600 text-sm text-center">{{ mediaTypeMap[history.media_type] }}</p>
          <!-- 视频播放图标 -->
          <div class="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
            <div class="w-12 h-12 bg-white/90 rounded-full flex items-center justify-center shadow-lg">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6 text-blue-600">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 010 1.971l-11.54 6.347a1.125 1.125 0 01-1.667-.985V5.653z" />
              </svg>
            </div>
          </div>
        </div>
        
        <!-- 图片历史记录 -->
        <img 
          v-else
          :src="history.result_url" 
          :alt="`修复结果 ${index + 1}`" 
          class="w-full h-full object-cover transform group-hover:scale-105 transition-transform duration-700 ease-in-out" 
        />
        
        <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-end p-4">
          <p class="text-white font-medium text-sm font-serif-title mb-1">
            {{ getOperationName(history.operation_type) }}
          </p>
          <p class="text-white/60 text-xs mb-1">
            {{ formatDate(history.created_at) }}
          </p>
          <p class="text-white/70 text-xs mb-2">
            {{ mediaTypeMap[history.media_type] || history.media_type }}
          </p>
          <div class="flex items-center justify-between">
            <span class="text-white/80 text-xs bg-primary-500/30 px-2 py-1 rounded-full">
              {{ history.task_id ? `任务 #${history.task_id}` : '单步操作' }}
            </span>
            <div class="flex items-center gap-2">
              <!-- 删除按钮 -->
              <button 
                @click.stop="confirmDeleteHistory(history)"
                class="w-8 h-8 rounded-full bg-red-500/30 flex items-center justify-center backdrop-blur-sm hover:bg-red-500/50 transition-colors"
              >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4 text-white">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                </svg>
              </button>
              <!-- 查看详情按钮 -->
              <div class="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center backdrop-blur-sm">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4 text-white">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Detail Modal -->
    <div v-if="selectedHistory" class="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-3xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <!-- Header -->
        <div class="sticky top-0 bg-white border-b border-gray-200 p-6 rounded-t-3xl flex justify-between items-center">
          <div>
            <h2 class="text-xl font-serif-title font-bold text-gray-900">{{ getOperationName(selectedHistory.operation_type) }}</h2>
            <p class="text-gray-500 text-sm">{{ formatDate(selectedHistory.created_at) }}</p>
          </div>
          <div class="flex gap-3">
            <!-- 跳转到对应模块按钮 -->
            <button 
              @click="navigateToModule(selectedHistory)"
              class="px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg text-sm font-medium transition-colors shadow-md hover:shadow-lg flex items-center gap-2"
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
                <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 6H5.25A2.25 2.25 0 0 0 3 8.25v10.5A2.25 2.25 0 0 0 5.25 21h10.5A2.25 2.25 0 0 0 18 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
              </svg>
              跳转到{{ getOperationName(selectedHistory.operation_type) }}模块
            </button>
            
            <button @click="closeDetail" class="w-10 h-10 rounded-full bg-gray-100 hover:bg-gray-200 flex items-center justify-center transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5 text-gray-600">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Content -->
        <div class="p-6 space-y-6">
          <!-- 音频历史记录详情 -->
          <div v-if="selectedHistory.media_type === 'audio' || selectedHistory.result_url?.endsWith('.wav') || selectedHistory.result_url?.endsWith('.mp3') || selectedHistory.operation_type === 'voice' || selectedHistory.operation_type === 'voice_clone' || selectedHistory.operation_type === 'tts'" class="space-y-4">
            <div class="bg-gray-50 rounded-2xl p-6">
              <h3 class="text-lg font-medium text-gray-900 mb-4">音频播放</h3>
              <div class="space-y-3">
                <!-- 错误状态 -->
                <div v-if="audioError" class="bg-red-50 border border-red-200 rounded-xl p-4">
                  <div class="flex items-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5 text-red-500">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                    </svg>
                    <span class="text-red-700 text-sm font-medium">{{ audioError }}</span>
                  </div>
                </div>
                
                <!-- 加载状态 -->
                <div v-if="audioLoading" class="flex items-center gap-3 text-blue-600">
                  <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                  <span class="text-sm">音频加载中...</span>
                </div>
                
                <!-- 音频播放器 -->
                <audio 
                  ref="audioPlayer"
                  controls 
                  class="w-full mb-2"
                  @error="handleAudioError"
                  @canplay="handleAudioCanPlay"
                  @loadstart="handleAudioLoadStart"
                  @stalled="handleAudioStalled"
                  preload="metadata"
                >
                  <source :src="selectedHistory.result_url" type="audio/wav">
                  <source :src="selectedHistory.result_url" type="audio/mpeg">
                  <source :src="selectedHistory.result_url" type="audio/mp3">
                  <source :src="selectedHistory.result_url" type="audio/ogg">
                  您的浏览器不支持音频播放。
                </audio>
                

              </div>
            </div>
          </div>
          
          <!-- 视频历史记录详情 -->
          <div v-else-if="selectedHistory.media_type === 'video' || selectedHistory.result_url?.endsWith('.mp4') || selectedHistory.result_url?.endsWith('.webm') || selectedHistory.operation_type === 'live_portrait' || selectedHistory.operation_type === 'liveportrait' || selectedHistory.operation_type === 'liveportrait_video'" class="space-y-4">
            <div class="bg-gray-50 rounded-2xl p-6">
              <h3 class="text-lg font-medium text-gray-900 mb-4">视频播放</h3>
              <div class="space-y-3">
                <!-- 视频播放器 -->
                <video 
                  ref="videoPlayer"
                  controls 
                  class="w-full max-w-2xl mx-auto rounded-lg shadow-lg"
                  preload="metadata"
                >
                  <source :src="selectedHistory.result_url" type="video/mp4">
                  <source :src="selectedHistory.result_url" type="video/webm">
                  您的浏览器不支持视频播放。
                </video>
                

              </div>
            </div>
          </div>
          
          <!-- 图片历史记录详情 -->
          <div v-else>
            <ImageCompare 
              :beforeImage="selectedHistory.input_url" 
              :afterImage="selectedHistory.result_url"
              labelBefore="修复前"
              labelAfter="修复后"
              :enableDownload="true"
              @download="downloadHistoryResult"
            />
          </div>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="bg-gray-50 rounded-2xl p-4">
              <h3 class="text-lg font-medium text-gray-900 mb-3">操作信息</h3>
              <div class="space-y-2">
                <div class="flex justify-between">
                  <span class="text-gray-500">媒体类型:</span>
                  <span class="font-medium text-gray-900">{{ mediaTypeMap[selectedHistory.media_type] || selectedHistory.media_type }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-500">操作类型:</span>
                  <span class="font-medium text-gray-900">{{ getOperationName(selectedHistory.operation_type) }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-500">功能模块:</span>
                  <span class="font-medium text-gray-900">{{ getOperationName(selectedHistory.operation_type) }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-500">操作时间:</span>
                  <span class="font-medium text-gray-900">{{ formatDate(selectedHistory.created_at) }}</span>
                </div>
                <div v-if="selectedHistory.task_id" class="flex justify-between">
                  <span class="text-gray-500">任务ID:</span>
                  <span class="font-medium text-gray-900">#{{ selectedHistory.task_id }}</span>
                </div>

              </div>
            </div>
            
            <div v-if="selectedHistory.params" class="bg-gray-50 rounded-2xl p-4">
              <h3 class="text-lg font-medium text-gray-900 mb-3">操作参数</h3>
              <div class="space-y-2">
                <div v-for="(value, key) in selectedHistory.params" :key="key" class="flex justify-between">
                  <span class="text-gray-500">{{ key }}:</span>
                  <span class="font-medium text-gray-900">{{ JSON.stringify(value) }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 操作按钮 -->
          <div class="flex gap-3 justify-end pt-4 border-t border-gray-200">
            <button 
              @click="deleteHistory"
              class="px-6 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg text-sm font-medium transition-colors shadow-md hover:shadow-lg flex items-center gap-2"
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
                <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
              </svg>
              删除记录
            </button>
            <button 
              @click="downloadHistoryResult"
              class="px-6 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg text-sm font-medium transition-colors shadow-md hover:shadow-lg flex items-center gap-2"
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12M12 16.5V12.75" />
              </svg>
              下载结果
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
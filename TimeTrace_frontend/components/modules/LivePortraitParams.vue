<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';

// 定义接口
export interface LivePortraitParamsType {
  drivingAudio: File | null;
  drivingVideo: File | null; // 新增：驱动视频
  relativeMotion: boolean; // 相对运动 (保留原图头部姿态)
  pasteBack: boolean;      // 贴回原图 (防止背景扭曲)
  expressionScale: number; // 表情夸张程度
}

const props = defineProps<{
  params: LivePortraitParamsType;
}>();

const emit = defineEmits<{
  (e: 'update:params', value: LivePortraitParamsType): void;
}>();

// 本地状态
const localParams = computed({
  get: () => props.params,
  set: (value) => emit('update:params', value)
});

const audioInput = ref<HTMLInputElement | null>(null);
const videoInput = ref<HTMLInputElement | null>(null);
const audioFileName = ref<string>('');
const videoFileName = ref<string>('');
const audioDuration = ref<string>('');
const videoDuration = ref<string>('');
const isDraggingAudio = ref(false);
const isDraggingVideo = ref(false);
const audioUrl = ref<string | null>(null);
const videoUrl = ref<string | null>(null);

// 触发文件选择
const triggerAudioUpload = () => {
  audioInput.value?.click();
};

const triggerVideoUpload = () => {
  videoInput.value?.click();
};

// 处理文件上传
const handleAudioChange = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files[0]) {
    processAudioFile(target.files[0]);
  }
};

const handleVideoChange = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files[0]) {
    processVideoFile(target.files[0]);
  }
};

const handleAudioDrop = (e: DragEvent) => {
  isDraggingAudio.value = false;
  if (e.dataTransfer?.files && e.dataTransfer.files[0]) {
    processAudioFile(e.dataTransfer.files[0]);
  }
};

const handleVideoDrop = (e: DragEvent) => {
  isDraggingVideo.value = false;
  if (e.dataTransfer?.files && e.dataTransfer.files[0]) {
    processVideoFile(e.dataTransfer.files[0]);
  }
};

const processAudioFile = (file: File) => {
  if (!file.type.startsWith('audio/')) {
    alert('请上传音频文件');
    return;
  }
  
  const newParams = { ...localParams.value };
  newParams.drivingAudio = file;
  emit('update:params', newParams);

  audioFileName.value = file.name;
  
  // 生成预览 URL
  if (audioUrl.value) URL.revokeObjectURL(audioUrl.value);
  audioUrl.value = URL.createObjectURL(file);
  
  // 获取时长
  const audio = new Audio(audioUrl.value);
  audio.onloadedmetadata = () => {
    const m = Math.floor(audio.duration / 60);
    const s = Math.floor(audio.duration % 60);
    audioDuration.value = `${m}:${s.toString().padStart(2, '0')}`;
  };
};

const processVideoFile = (file: File) => {
  if (!file.type.startsWith('video/')) {
    alert('请上传视频文件');
    return;
  }
  
  const newParams = { ...localParams.value };
  newParams.drivingVideo = file;
  emit('update:params', newParams);

  videoFileName.value = file.name;
  
  // 生成预览 URL
  if (videoUrl.value) URL.revokeObjectURL(videoUrl.value);
  videoUrl.value = URL.createObjectURL(file);
  
  // 获取时长
  const video = document.createElement('video');
  video.src = videoUrl.value;
  video.onloadedmetadata = () => {
    const m = Math.floor(video.duration / 60);
    const s = Math.floor(video.duration % 60);
    videoDuration.value = `${m}:${s.toString().padStart(2, '0')}`;
  };
};

const removeAudio = (e: Event) => {
  e.stopPropagation();
  const newParams = { ...localParams.value };
  newParams.drivingAudio = null;
  emit('update:params', newParams);
  
  audioFileName.value = '';
  audioDuration.value = '';
  if (audioUrl.value) {
    URL.revokeObjectURL(audioUrl.value);
    audioUrl.value = null;
  }
  if (audioInput.value) audioInput.value.value = '';
};

const removeVideo = (e: Event) => {
  e.stopPropagation();
  const newParams = { ...localParams.value };
  newParams.drivingVideo = null;
  emit('update:params', newParams);
  
  videoFileName.value = '';
  videoDuration.value = '';
  if (videoUrl.value) {
    URL.revokeObjectURL(videoUrl.value);
    videoUrl.value = null;
  }
  if (videoInput.value) videoInput.value.value = '';
};

onUnmounted(() => {
  if (audioUrl.value) URL.revokeObjectURL(audioUrl.value);
  if (videoUrl.value) URL.revokeObjectURL(videoUrl.value);
});
</script>

<template>
  <div class="bg-white/90 backdrop-blur-md p-6 rounded-[1.5rem] shadow-xl border border-indigo-100/50 space-y-6 relative overflow-hidden transition-all duration-300 hover:shadow-2xl hover:shadow-indigo-500/10">
    
    <div class="absolute -top-10 -right-10 w-32 h-32 bg-indigo-200/20 rounded-full blur-3xl pointer-events-none animate-pulse-slow"></div>
    <div class="absolute bottom-0 left-0 w-24 h-24 bg-purple-100/30 rounded-full blur-2xl pointer-events-none"></div>

    <div class="flex items-center gap-3 border-b border-indigo-50 pb-4 relative z-10">
      <div class="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-100 to-purple-50 flex items-center justify-center text-indigo-600 shadow-sm border border-indigo-100">
        <FontAwesomeIcon icon="fa-solid fa-video" class="text-lg" />
      </div>
      <div>
        <h3 class="text-lg font-bold text-gray-800 tracking-wide">灵动 · 人像复活</h3>
        <p class="text-xs text-indigo-500/80 font-medium tracking-wider uppercase">LivePortrait Talking Head</p>
      </div>
    </div>

    <div class="space-y-5 relative z-10">
      
      <div>
        <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 ml-1">驱动视频 (Driving Video)</label>
        
        <div 
          class="relative group cursor-pointer"
          @click="triggerVideoUpload"
          @dragover.prevent="isDraggingVideo = true"
          @dragleave.prevent="isDraggingVideo = false"
          @drop.prevent="handleVideoDrop"
        >
          <input type="file" ref="videoInput" accept="video/*" class="hidden" @change="handleVideoChange" />
          
          <div 
            class="w-full h-24 rounded-2xl border-2 border-dashed transition-all duration-300 flex items-center justify-center overflow-hidden bg-slate-50/50"
            :class="[
              isDraggingVideo ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200 hover:border-indigo-300 hover:bg-white',
              localParams.drivingVideo ? 'border-indigo-200 bg-indigo-50/30' : ''
            ]"
          >
            <div v-if="!localParams.drivingVideo" class="text-center space-y-2 pointer-events-none">
              <div class="w-10 h-10 mx-auto rounded-full bg-white shadow-sm flex items-center justify-center text-indigo-400 group-hover:scale-110 transition-transform duration-300">
                <FontAwesomeIcon icon="fa-solid fa-video" />
              </div>
              <p class="text-xs text-gray-500 font-medium">点击或拖拽上传驱动视频</p>
            </div>

            <div v-else class="w-full h-full px-4 flex items-center justify-between">
              <div class="flex items-center gap-3 overflow-hidden">
                <div class="w-10 h-10 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center text-white shadow-md animate-spin-slow-pause">
                  <FontAwesomeIcon icon="fa-solid fa-film" />
                </div>
                <div class="flex-1 min-w-0 text-left">
                  <p class="text-sm font-bold text-gray-800 truncate">{{ videoFileName }}</p>
                  <p class="text-xs text-indigo-500 font-mono">{{ videoDuration || 'Ready' }}</p>
                </div>
              </div>
              
              <div class="flex items-center gap-2">
                 <video v-if="videoUrl" :src="videoUrl" controls class="hidden" preload="metadata"></video>
                 
                 <button @click="removeVideo" class="w-8 h-8 rounded-full bg-white hover:bg-red-50 text-gray-400 hover:text-red-500 transition-colors shadow-sm border border-gray-100 flex items-center justify-center z-20">
                    <FontAwesomeIcon icon="fa-solid fa-xmark" />
                 </button>
              </div>
              
              <div class="absolute bottom-0 left-0 right-0 h-1 flex items-end gap-1 justify-center opacity-30">
                 <div class="w-1 bg-indigo-500 animate-wave" style="animation-delay: 0.1s"></div>
                 <div class="w-1 bg-indigo-500 animate-wave" style="animation-delay: 0.2s"></div>
                 <div class="w-1 bg-indigo-500 animate-wave" style="animation-delay: 0.3s"></div>
                 <div class="w-1 bg-indigo-500 animate-wave" style="animation-delay: 0.1s"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div>
        <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 ml-1">驱动音频 (Driving Audio)</label>
        
        <div 
          class="relative group cursor-pointer"
          @click="triggerAudioUpload"
          @dragover.prevent="isDraggingAudio = true"
          @dragleave.prevent="isDraggingAudio = false"
          @drop.prevent="handleAudioDrop"
        >
          <input type="file" ref="audioInput" accept="audio/*" class="hidden" @change="handleAudioChange" />
          
          <div 
            class="w-full h-24 rounded-2xl border-2 border-dashed transition-all duration-300 flex items-center justify-center overflow-hidden bg-slate-50/50"
            :class="[
              isDraggingAudio ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200 hover:border-indigo-300 hover:bg-white',
              localParams.drivingAudio ? 'border-indigo-200 bg-indigo-50/30' : ''
            ]"
          >
            <div v-if="!localParams.drivingAudio" class="text-center space-y-2 pointer-events-none">
              <div class="w-10 h-10 mx-auto rounded-full bg-white shadow-sm flex items-center justify-center text-indigo-400 group-hover:scale-110 transition-transform duration-300">
                <FontAwesomeIcon icon="fa-solid fa-microphone-lines" />
              </div>
              <p class="text-xs text-gray-500 font-medium">点击或拖拽上传音频文件</p>
            </div>

            <div v-else class="w-full h-full px-4 flex items-center justify-between">
              <div class="flex items-center gap-3 overflow-hidden">
                <div class="w-10 h-10 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center text-white shadow-md animate-spin-slow-pause">
                  <FontAwesomeIcon icon="fa-solid fa-music" />
                </div>
                <div class="flex-1 min-w-0 text-left">
                  <p class="text-sm font-bold text-gray-800 truncate">{{ audioFileName }}</p>
                  <p class="text-xs text-indigo-500 font-mono">{{ audioDuration || 'Ready' }}</p>
                </div>
              </div>
              
              <div class="flex items-center gap-2">
                 <audio v-if="audioUrl" :src="audioUrl" controls class="hidden"></audio>
                 
                 <button @click="removeAudio" class="w-8 h-8 rounded-full bg-white hover:bg-red-50 text-gray-400 hover:text-red-500 transition-colors shadow-sm border border-gray-100 flex items-center justify-center z-20">
                    <FontAwesomeIcon icon="fa-solid fa-xmark" />
                 </button>
              </div>
              
              <div class="absolute bottom-0 left-0 right-0 h-1 flex items-end gap-1 justify-center opacity-30">
                 <div class="w-1 bg-indigo-500 animate-wave" style="animation-delay: 0.1s"></div>
                 <div class="w-1 bg-indigo-500 animate-wave" style="animation-delay: 0.2s"></div>
                 <div class="w-1 bg-indigo-500 animate-wave" style="animation-delay: 0.3s"></div>
                 <div class="w-1 bg-indigo-500 animate-wave" style="animation-delay: 0.1s"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div>
        <div class="flex justify-between items-center mb-2">
            <label class="text-xs font-bold text-gray-400 uppercase tracking-wider ml-1">表情幅度 (Expression)</label>
            <span class="text-xs font-bold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-100">x{{ localParams.expressionScale.toFixed(1) }}</span>
        </div>
        <div class="relative flex items-center group">
             <input 
                type="range" 
                v-model.number="localParams.expressionScale" 
                min="0.5" max="1.5" step="0.1"
                class="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-indigo-500 z-10 relative"
            />
            <div class="absolute top-1/2 left-0 w-full h-1.5 bg-gray-200 rounded-lg overflow-hidden">
                <div class="h-full bg-gradient-to-r from-indigo-300 to-purple-400" :style="{ width: ((localParams.expressionScale - 0.5) / 1.0 * 100) + '%' }"></div>
            </div>
        </div>
        <div class="flex justify-between text-[10px] text-gray-400 mt-2 font-medium">
            <span>克制</span>
            <span>自然</span>
            <span>夸张</span>
        </div>
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div 
            class="p-3 rounded-xl border transition-all duration-200 cursor-pointer flex items-center justify-between"
            :class="localParams.relativeMotion ? 'bg-indigo-50 border-indigo-200' : 'bg-gray-50 border-gray-100 hover:bg-gray-100'"
            @click="localParams.relativeMotion = !localParams.relativeMotion"
        >
            <div class="flex flex-col">
                <span class="text-sm font-bold" :class="localParams.relativeMotion ? 'text-indigo-700' : 'text-gray-600'">相对运动</span>
                <span class="text-[10px] text-gray-400">保留原图头姿</span>
            </div>
            <div class="w-8 h-4 rounded-full relative transition-colors duration-300" :class="localParams.relativeMotion ? 'bg-indigo-500' : 'bg-gray-300'">
                <div class="absolute top-0.5 left-0.5 w-3 h-3 bg-white rounded-full shadow-sm transition-transform duration-300" :class="localParams.relativeMotion ? 'translate-x-4' : 'translate-x-0'"></div>
            </div>
        </div>

        <div 
            class="p-3 rounded-xl border transition-all duration-200 cursor-pointer flex items-center justify-between"
            :class="localParams.pasteBack ? 'bg-purple-50 border-purple-200' : 'bg-gray-50 border-gray-100 hover:bg-gray-100'"
            @click="localParams.pasteBack = !localParams.pasteBack"
        >
            <div class="flex flex-col">
                <span class="text-sm font-bold" :class="localParams.pasteBack ? 'text-purple-700' : 'text-gray-600'">背景保护</span>
                <span class="text-[10px] text-gray-400">防止背景扭曲</span>
            </div>
             <div class="w-8 h-4 rounded-full relative transition-colors duration-300" :class="localParams.pasteBack ? 'bg-purple-500' : 'bg-gray-300'">
                <div class="absolute top-0.5 left-0.5 w-3 h-3 bg-white rounded-full shadow-sm transition-transform duration-300" :class="localParams.pasteBack ? 'translate-x-4' : 'translate-x-0'"></div>
            </div>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
/* 简单的声波动画 */
@keyframes wave {
  0%, 100% { height: 4px; }
  50% { height: 16px; }
}

.animate-wave {
  animation: wave 1s infinite ease-in-out;
}

.animate-pulse-slow {
    animation: pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

/* 缓慢旋转并在暂停时保持 */
@keyframes spin-slow {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}
.animate-spin-slow-pause {
    animation: spin-slow 8s linear infinite;
}
</style>
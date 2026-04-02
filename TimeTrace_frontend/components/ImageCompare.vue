<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';

const props = defineProps({
  beforeImage: { type: String, required: true },
  afterImage: { type: String, required: true },
  labelBefore: { type: String, default: "修复前" },
  labelAfter: { type: String, default: "修复后" },
  enableDownload: { type: Boolean, default: false }
});

const emit = defineEmits(['download']);

const sliderPosition = ref(50);
const container = ref<HTMLElement | null>(null);
const isDragging = ref(false);
const beforeImageLoaded = ref(false);
const afterImageLoaded = ref(false);

// 监听图片变化，重置加载状态
watch(() => [props.beforeImage, props.afterImage], () => {
  beforeImageLoaded.value = false;
  afterImageLoaded.value = false;
});

const handleMove = (event: MouseEvent | TouchEvent) => {
  if (!container.value) return;

  const containerRect = container.value.getBoundingClientRect();
  let clientX;

  if (event instanceof MouseEvent) {
    clientX = event.clientX;
  } else {
    clientX = event.touches[0].clientX;
  }

  const position = ((clientX - containerRect.left) / containerRect.width) * 100;
  sliderPosition.value = Math.min(100, Math.max(0, position));
};

const handleStart = () => {
  isDragging.value = true;
};

const handleEnd = () => {
  isDragging.value = false;
};

const handleWindowMove = (e: MouseEvent | TouchEvent) => {
  if (isDragging.value) {
    handleMove(e);
  }
};

const handleBeforeImageLoad = () => {
  beforeImageLoaded.value = true;
};

const handleAfterImageLoad = () => {
  afterImageLoaded.value = true;
};

const handleDownload = () => {
  emit('download', props.afterImage);
};

onMounted(() => {
  window.addEventListener('mousemove', handleWindowMove);
  window.addEventListener('touchmove', handleWindowMove);
  window.addEventListener('mouseup', handleEnd);
  window.addEventListener('touchend', handleEnd);
});

onUnmounted(() => {
  window.removeEventListener('mousemove', handleWindowMove);
  window.removeEventListener('touchmove', handleWindowMove);
  window.removeEventListener('mouseup', handleEnd);
  window.removeEventListener('touchend', handleEnd);
});
</script>

<template>
  <div 
    ref="container"
    class="relative w-full h-[600px] overflow-hidden rounded-2xl shadow-2xl select-none group cursor-ew-resize bg-stone-900 border border-gray-100"
    @mousedown="handleStart"
    @touchstart="handleStart"
  >
      <!-- 加载状态 -->
      <div v-if="!beforeImageLoaded || !afterImageLoaded" class="absolute inset-0 flex items-center justify-center bg-stone-900 z-10">
        <div class="text-center text-white">
          <svg class="animate-spin h-8 w-8 text-primary-400 mx-auto mb-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p class="text-sm">加载图片中...</p>
        </div>
      </div>

      <!-- After Image (Background) -->
      <div 
        class="absolute inset-0 flex items-center justify-center bg-stone-900"
        @click="enableDownload ? handleDownload() : null"
        :class="{ 'cursor-pointer hover:opacity-90 transition-opacity': enableDownload }"
      >
        <img 
          :src="afterImage" 
          alt="After" 
          class="max-w-full max-h-full object-contain"
          draggable="false"
          @load="handleAfterImageLoad"
          :class="{ 'opacity-0': !afterImageLoaded }"
        />
        <!-- 下载提示 -->
        <div v-if="enableDownload" class="absolute bottom-4 right-4 bg-black/60 backdrop-blur-md border border-white/20 text-white px-3 py-1 rounded-full text-xs font-medium pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-300">
          <FontAwesomeIcon icon="fa-solid fa-download" class="mr-1" /> 点击下载
        </div>
      </div>
      
      <!-- Label After -->
      <div class="absolute top-6 right-6 bg-black/40 backdrop-blur-md border border-white/10 text-white px-4 py-1.5 rounded-full text-xs font-medium z-10 pointer-events-none tracking-wide uppercase">
        {{ labelAfter }}
      </div>

      <!-- Before Image (Foreground - Clipped) -->
      <div 
        class="absolute top-0 left-0 w-full h-full overflow-hidden bg-stone-900"
        :style="{ clipPath: `polygon(0 0, ${sliderPosition}% 0, ${sliderPosition}% 100%, 0 100%)` }"
      >
        <div class="absolute inset-0 flex items-center justify-center">
          <img 
            :src="beforeImage" 
            alt="Before" 
            class="max-w-full max-h-full object-contain"
            draggable="false"
            @load="handleBeforeImageLoad"
            :class="{ 'opacity-0': !beforeImageLoaded }"
          />
        </div>
        <!-- Label Before -->
        <div class="absolute top-6 left-6 bg-black/40 backdrop-blur-md border border-white/10 text-white px-4 py-1.5 rounded-full text-xs font-medium pointer-events-none tracking-wide uppercase">
          {{ labelBefore }}
        </div>
      </div>

      <!-- Slider Line -->
      <div 
        class="absolute top-0 bottom-0 w-1 bg-white cursor-ew-resize shadow-[0_0_20px_rgba(0,0,0,0.5)] z-20"
        :style="{ left: `${sliderPosition}%` }"
      >
        <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-10 h-10 bg-primary-400 border-2 border-white rounded-full shadow-lg flex items-center justify-center text-white hover:scale-110 transition-transform duration-200">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="w-5 h-5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 15 12 18.75 15.75 15m-7.5-6L12 5.25 15.75 9" />
          </svg>
        </div>
      </div>

  </div>
</template>
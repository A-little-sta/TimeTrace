<template>
  <div 
    ref="containerRef"
    class="relative w-full rounded-[2.5rem] overflow-hidden shadow-2xl group select-none cursor-crosshair bg-gray-100 border border-gray-200"
    :class="className"
    @mouseenter="handleMouseEnter"
    @mouseleave="handleMouseLeave"
    @mousemove="handleMouseMove"
    @touchmove="handleTouchMove"
    @click="handleClick"
  >
    <!-- After Image (Background) -->
    <img 
      :src="afterImage" 
      alt="After" 
      class="absolute inset-0 w-full h-full object-cover transition-transform duration-[2s] ease-out group-hover:scale-105" 
      draggable="false"
    />

    <!-- Before Image (Clipped) -->
    <div 
      class="absolute inset-0 w-full h-full bg-white/5"
      :style="{ clipPath: `inset(0 ${100 - sliderPosition}% 0 0)` }"
    >
      <img 
        :src="beforeImage" 
        alt="Before" 
        class="absolute inset-0 w-full h-full object-cover" 
        draggable="false"
      />
      
      <!-- Overlay Badges -->
      <div class="absolute top-6 left-6 px-3 py-1 bg-black/60 backdrop-blur-md rounded-full text-white/90 text-xs font-bold tracking-wider uppercase border border-white/10 shadow-lg">
        修复前
      </div>
    </div>

    <div class="absolute top-6 right-6 px-3 py-1 bg-white/30 backdrop-blur-md rounded-full text-white text-xs font-bold tracking-wider uppercase border border-white/20 shadow-lg">
      修复后
    </div>

    <!-- Slider Line -->
    <div 
      class="absolute top-0 bottom-0 w-1 bg-white/90 cursor-ew-resize z-20 shadow-[0_0_20px_rgba(0,0,0,0.5)]"
      :style="{ left: `${sliderPosition}%` }"
      @mousedown="handleMouseDown"
      @touchstart="handleMouseDown"
    >
      <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-12 h-12 bg-white rounded-full flex items-center justify-center shadow-xl text-primary-600 transition-transform hover:scale-110 active:scale-95">
         <FontAwesomeIcon icon="fa-solid fa-wand-magic-sparkles" />
      </div>
    </div>

    <!-- Text Content -->
    <div v-if="title || description" class="absolute bottom-10 left-10 md:left-14 z-10 max-w-xl text-white pointer-events-none">
      <div class="inline-block px-3 py-1 mb-4 rounded-full bg-black/30 backdrop-blur-md border border-white/20 text-xs font-bold uppercase tracking-widest text-primary-200">
         AI 效果预览
      </div>
      <h2 v-if="title" class="text-4xl md:text-5xl font-serif font-bold mb-2 drop-shadow-lg text-white">{{ title }}</h2>
      <p v-if="description" class="text-lg text-white/90 font-light drop-shadow-md">{{ description }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';

const props = defineProps({
  beforeImage: { type: String, required: true },
  afterImage: { type: String, required: true },
  title: String,
  description: String,
  autoAnimate: { type: Boolean, default: true },
  className: { type: String, default: "h-[500px]" }
});

const sliderPosition = ref(50);
const isHovering = ref(false);
const isDragging = ref(false);
const containerRef = ref<HTMLElement | null>(null);
let animationFrameId: number | null = null;

const startAnimation = () => {
  if (!props.autoAnimate) return;

  let direction = 1;
  let speed = 0.2;
  let currentPos = sliderPosition.value;

  const animate = () => {
    if (isHovering.value || isDragging.value) return;

    currentPos += speed * direction;
    if (currentPos >= 85 || currentPos <= 15) {
      direction *= -1;
    }
    sliderPosition.value = currentPos;
    animationFrameId = requestAnimationFrame(animate);
  };

  animationFrameId = requestAnimationFrame(animate);
};

const stopAnimation = () => {
  if (animationFrameId !== null) {
    cancelAnimationFrame(animationFrameId);
    animationFrameId = null;
  }
};

onMounted(() => {
  startAnimation();
  window.addEventListener('mouseup', handleGlobalMouseUp);
});

onUnmounted(() => {
  stopAnimation();
  window.removeEventListener('mouseup', handleGlobalMouseUp);
});

watch([isHovering, isDragging], ([hover, drag]) => {
  if (!hover && !drag) {
    startAnimation();
  } else {
    stopAnimation();
  }
});

const handleMove = (clientX: number) => {
  if (containerRef.value) {
    const rect = containerRef.value.getBoundingClientRect();
    const x = Math.max(0, Math.min(clientX - rect.left, rect.width));
    const percentage = (x / rect.width) * 100;
    sliderPosition.value = percentage;
  }
};

const handleMouseEnter = () => isHovering.value = true;
const handleMouseLeave = () => {
  isHovering.value = false;
  isDragging.value = false;
};
const handleMouseDown = () => isDragging.value = true;
const handleGlobalMouseUp = () => isDragging.value = false;

const handleMouseMove = (e: MouseEvent) => {
  if (isDragging.value) handleMove(e.clientX);
};
const handleTouchMove = (e: TouchEvent) => {
  handleMove(e.touches[0].clientX);
};
const handleClick = (e: MouseEvent) => {
  handleMove(e.clientX);
};
</script>

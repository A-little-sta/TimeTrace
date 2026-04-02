<template>
  <div class="relative w-full h-[450px] md:h-[500px] rounded-[2.5rem] overflow-hidden shadow-xl group select-none bg-gray-900">
    
    <!-- 背景层：修复前 (Before) -->
    <img 
      :src="currentSlide.before" 
      class="absolute inset-0 w-full h-full object-cover transition-transform duration-[2000ms] ease-out group-hover:scale-105"
      alt="Before"
    />

    <!-- 遮罩层：修复后 (After) -->
    <!-- 使用 clip-path 动态裁剪，实现扫描效果 -->
    <div 
      class="absolute inset-0 w-full h-full bg-black/5 transition-all duration-75 ease-linear" 
      :style="{ clipPath: `inset(0 0 0 ${scanPosition}%)` }"
    >
      <img 
        :src="currentSlide.after" 
        class="absolute inset-0 w-full h-full object-cover"
        alt="After" 
      />
      
      <!-- 扫描光束线 -->
      <div class="absolute top-0 bottom-0 left-0 w-1 bg-white/60 shadow-[0_0_20px_rgba(255,255,255,0.9)] z-10"></div>
      
      <!-- 扫描手柄图标 -->
      <div class="absolute top-1/2 left-0 transform -translate-x-1/2 -translate-y-1/2 w-10 h-10 bg-white rounded-full flex items-center justify-center shadow-lg text-primary z-20">
        <i class="fa-solid fa-wand-magic-sparkles text-sm"></i>
      </div>
    </div>

    <!-- 底部渐变遮罩 (为了让文字更清晰) -->
    <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent pointer-events-none"></div>

    <!-- 文字浮层 -->
    <div class="absolute bottom-10 left-8 md:left-16 z-30 max-w-2xl text-white pointer-events-none">
      <div class="inline-block px-3 py-1 mb-4 rounded-full bg-white/20 backdrop-blur-md border border-white/20 text-[10px] font-bold uppercase tracking-widest text-white animate-fade-in">
        AI Restoration Showcase
      </div>
      
      <transition name="slide-up" mode="out-in">
        <div :key="currentSlide.id">
          <h2 class="text-3xl md:text-5xl font-serif font-bold mb-3 drop-shadow-lg leading-tight">
            {{ currentSlide.title }}
          </h2>
          <p class="text-base md:text-lg text-white/80 font-light drop-shadow-md leading-relaxed">
            {{ currentSlide.desc }}
          </p>
        </div>
      </transition>
    </div>

    <!-- 进度/切换指示器 -->
    <div class="absolute bottom-10 right-8 md:right-16 flex gap-3 z-30">
      <button 
        v-for="(slide, index) in slides" 
        :key="index" 
        @click="manualSwitch(index)"
        class="h-1.5 rounded-full transition-all duration-300 backdrop-blur-sm cursor-pointer hover:bg-white"
        :class="currentIndex === index ? 'w-8 bg-white' : 'w-2 bg-white/30'"
      ></button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { SLIDES } from '../constants';

// 使用全局定义的SLIDES常量（包含4张轮播图）
const slides = SLIDES;

const currentIndex = ref(0);
const scanPosition = ref(0); // 0 到 100 之间的数值，控制扫描线位置
const currentSlide = computed(() => slides[currentIndex.value]);
let animationFrame: number;
let isPaused = false;

// 核心动画循环
const animateScan = () => {
  const speed = 0.35; // 扫描速度
  
  const step = () => {
    if (!isPaused) {
      scanPosition.value -= speed;
      
      // 当扫描线跑出屏幕 (<=-20%)，切换下一张
      if (scanPosition.value <= -20) {
        nextSlide();
        scanPosition.value = 120; // 重置到右边屏幕外
      }
    }
    animationFrame = requestAnimationFrame(step);
  };
  step();
};

const nextSlide = () => {
  currentIndex.value = (currentIndex.value + 1) % slides.length;
};

// 手动切换
const manualSwitch = (index: number) => {
  currentIndex.value = index;
  scanPosition.value = 0; // 手动切换时停在最左边，方便查看对比
  // 暂停一小会儿自动播放，让用户看清楚
  isPaused = true;
  setTimeout(() => { isPaused = false }, 3000);
};

onMounted(() => {
  animateScan();
});

onUnmounted(() => {
  cancelAnimationFrame(animationFrame);
});
</script>

<style scoped>
/* 文字切换动画 */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}
.slide-up-enter-from {
  opacity: 0;
  transform: translateY(20px);
}
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

.animate-fade-in {
  animation: fadeIn 0.8s ease-out forwards;
}
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>
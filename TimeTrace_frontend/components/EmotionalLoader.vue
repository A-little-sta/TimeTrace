<template>
  <div class="fixed inset-0 bg-black/70 flex items-center justify-center z-50 backdrop-blur-sm transition-opacity duration-500" :class="show ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'">
    <div v-if="show && mounted" class="relative w-full max-w-sm mx-auto">
      <!-- Breathing Glow -->
      <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-72 h-72 rounded-full bg-gradient-to-r from-primary-400/30 to-purple-400/30 blur-3xl animate-pulse-slow"></div>

      <div class="relative bg-white rounded-[2rem] p-8 shadow-2xl text-center overflow-hidden border border-white/20">
        
        <!-- Icon -->
        <div class="w-20 h-20 mx-auto mb-8 rounded-2xl flex items-center justify-center shadow-inner relative z-10 ring-4 ring-white" :class="module.iconBg">
           <FontAwesomeIcon :icon="[module.iconName.split(' ')[0], module.iconName.split(' ')[1]]" class="text-4xl animate-bounce" :class="module.iconColor" />
        </div>

        <!-- Texts -->
        <div class="mb-10 h-20">
          <p class="text-xl font-serif text-gray-900 font-bold mb-2 transition-all duration-500 ease-in-out">
            {{ currentEmotionalText }}
          </p>
          <p class="text-sm text-gray-400 font-mono uppercase tracking-widest">
            {{ currentTechnicalText }}
          </p>
        </div>

        <!-- Progress Circle -->
        <div class="w-24 h-24 mx-auto relative mb-6">
          <svg class="w-full h-full -rotate-90" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="45" fill="none" stroke="#F3F4F6" stroke-width="6" />
            <circle 
              cx="50" 
              cy="50" 
              r="45" 
              fill="none" 
              stroke="url(#gradient)" 
              stroke-width="6" 
              stroke-linecap="round"
              stroke-dasharray="283"
              :stroke-dashoffset="progressOffset"
              class="transition-all duration-100 ease-linear"
            />
            <defs>
              <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#3B82F6" />
                <stop offset="100%" stop-color="#8B5CF6" />
              </linearGradient>
            </defs>
          </svg>
          <div class="absolute inset-0 flex items-center justify-center">
            <span class="text-xl font-bold text-gray-800 font-sans">{{ Math.round(progress) }}%</span>
          </div>
        </div>

        <div class="text-xs text-gray-400 font-medium">AI 正在云端施展魔法...</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, onUnmounted, onMounted } from 'vue';
import { ModuleConfig } from '../types';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';

const props = defineProps<{
  module: ModuleConfig;
  show: boolean;
}>();

const emit = defineEmits(['complete']);

const progress = ref(0);
const textIndex = ref(0);
const mounted = ref(false);

let progressInterval: any = null;
let textInterval: any = null;

const currentEmotionalText = computed(() => props.module.emotionalTexts[textIndex.value]);
const currentTechnicalText = computed(() => props.module.technicalTexts[textIndex.value % props.module.technicalTexts.length]);
const progressOffset = computed(() => 283 - (progress.value / 100) * 283);

onMounted(() => {
  mounted.value = true;
});

watch(() => props.show, (newShow) => {
  if (newShow) {
    progress.value = 0;
    textIndex.value = 0;
    
    // Start simulation
    progressInterval = setInterval(() => {
      progress.value = Math.min(progress.value + (progress.value < 80 ? Math.random() * 2 : Math.random() * 0.5), 100);
      if (progress.value >= 100) {
        clearInterval(progressInterval);
        emit('complete');
      }
    }, 50);

    textInterval = setInterval(() => {
      textIndex.value = (textIndex.value + 1) % props.module.emotionalTexts.length;
    }, 2500);

  } else {
    if (progressInterval) clearInterval(progressInterval);
    if (textInterval) clearInterval(textInterval);
  }
});

onUnmounted(() => {
  clearInterval(progressInterval);
  clearInterval(textInterval);
});
</script>

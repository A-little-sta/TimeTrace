<template>
  <div class="min-h-screen bg-[#F3F4F6] p-6 md:p-10 pb-20">
    <div class="max-w-7xl mx-auto space-y-12 animate-fade-in-up">
      <!-- Header -->
      <header class="flex flex-col sm:flex-row justify-between items-start sm:items-center py-4 gap-4">
      <div>
        <h1 class="font-serif text-4xl md:text-5xl bg-gradient-to-r from-primary-400 via-primary-500 to-primary-600 bg-clip-text text-transparent font-bold mb-3 tracking-tight">
          岁月笺影基于AI的多模态影像修复系统
        </h1>
        <p class="text-gray-500 font-light text-lg">让每一张老照片，都能再次诉说它的故事</p>
      </div>
      <button 
        class="hidden md:flex items-center gap-2 px-6 py-3 rounded-full bg-white border border-gray-200 text-sm font-semibold text-gray-600 hover:text-primary-600 hover:border-primary-200 hover:bg-primary-50 transition-all shadow-sm hover:shadow-md"
        @click="handleGuideClick"
      >
        <FontAwesomeIcon icon="fa-regular fa-circle-question" />
        <span>功能使用指南</span>
      </button>
    </header>

    <!-- Hero / Carousel Area -->
    <FeatureCarousel />

    <!-- Modules Grid -->
    <div>
      <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-8 gap-2">
        <h2 class="text-2xl font-bold text-gray-800 font-serif flex items-center gap-3">
          <span class="w-8 h-8 rounded-lg bg-primary-100 flex items-center justify-center text-primary-600 text-sm shadow-sm">
              <FontAwesomeIcon icon="fa-solid fa-shapes" />
          </span>
          修复工坊
        </h2>
        <span class="text-xs text-gray-400 uppercase tracking-widest font-bold">AI MODULES</span>
      </div>
      
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <!-- Guide Card -->
        <div 
          class="group relative bg-white rounded-[2rem] p-6 h-80 flex flex-col justify-between cursor-pointer transition-all duration-500 hover:-translate-y-2 hover:shadow-2xl border border-transparent hover:border-primary-200 overflow-hidden"
          @click="handleGuideClick"
        >
           <div class="absolute inset-0 bg-gradient-to-br from-blue-400 to-blue-100 opacity-0 group-hover:opacity-10 transition-opacity duration-500"></div>
           <div class="absolute -right-8 -top-8 w-32 h-32 rounded-full bg-blue-50 opacity-0 group-hover:opacity-20 transition-all duration-700 group-hover:scale-150"></div>
          
          <div class="w-16 h-16 rounded-2xl bg-blue-50 flex items-center justify-center text-3xl transition-all duration-300 group-hover:scale-110 shadow-sm z-10 text-blue-600">
            <FontAwesomeIcon icon="fa-solid fa-book-open" />
          </div>

          <div class="relative z-10 mt-6">
            <h3 class="font-serif text-2xl font-bold text-gray-800 mb-3 group-hover:text-blue-600 transition-colors">使用指南</h3>
            <p class="text-sm text-gray-500 leading-relaxed font-medium">了解每个功能的最佳使用场景，让 AI 修复效果更加出色。</p>
          </div>

          <div class="flex items-center justify-between mt-auto pt-6 border-t border-gray-50 z-10">
            <span class="text-[10px] font-bold uppercase tracking-widest text-gray-400 group-hover:text-gray-900 transition-colors">查看详情</span>
            <div class="w-10 h-10 rounded-full bg-gray-50 flex items-center justify-center group-hover:bg-gray-900 group-hover:text-white transition-all shadow-sm">
              <FontAwesomeIcon icon="fa-solid fa-arrow-right" class="text-sm" />
            </div>
          </div>
        </div>

        <!-- Actual Modules -->
        <ModuleCard 
          v-for="(module, index) in MODULES"
          :key="module.id" 
          :module="module" 
          :index="index" 
          @click="navigateToModule" 
        />
      </div>
    </div>
  </div>
</div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import ModuleCard from '../components/ModuleCard.vue';
import FeatureCarousel from '../components/FeatureCarousel.vue';
import { MODULES } from '../constants';

const router = useRouter();

const handleGuideClick = () => {
  router.push('/help-center');
};

const navigateToModule = (id: string) => {
  router.push(`/workshop/${id}`);
};
</script>

<style scoped>
/* 顺序入场动画 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fade-in-up {
  animation: fadeInUp 0.8s ease-out forwards;
}
</style>

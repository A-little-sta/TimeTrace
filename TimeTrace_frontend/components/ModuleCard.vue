<template>
  <div 
    class="group relative bg-white rounded-[2rem] p-6 h-80 flex flex-col justify-between cursor-pointer transition-all duration-500 hover:-translate-y-2 hover:shadow-2xl border border-transparent hover:border-primary-200 overflow-hidden"
    :style="{ animationDelay: `${index * 100}ms` }"
    @click="$emit('click', module.id)"
  >
    <!-- Background Gradients -->
    <div class="absolute inset-0 bg-gradient-to-br from-blue-400 to-blue-100 opacity-0 group-hover:opacity-10 transition-opacity duration-500"></div>
    <div class="absolute -right-8 -top-8 w-32 h-32 rounded-full bg-blue-50 opacity-0 group-hover:opacity-20 transition-all duration-700 group-hover:scale-150"></div>
    
    <!-- Icon -->
    <div class="w-16 h-16 rounded-2xl bg-blue-50 flex items-center justify-center text-3xl transition-all duration-300 group-hover:scale-110 shadow-sm z-10 text-blue-600">
      <template v-if="typeof module.icon === 'string'">
        <FontAwesomeIcon :icon="[module.icon.split(' ')[0], module.icon.split(' ')[1]]" class="w-8 h-8" />
      </template>
      <template v-else>
        <!-- 如果是VNode直接渲染 -->
        <component :is="module.icon" class="w-8 h-8" />
      </template>
    </div>

    <!-- Content -->
    <div class="relative z-10 mt-6">
      <h3 class="font-serif text-2xl font-bold text-gray-800 mb-3 group-hover:text-blue-600 transition-colors">
        {{ module.name }}
      </h3>
      <p class="text-sm text-gray-500 leading-relaxed line-clamp-3 font-medium">
        {{ module.description }}
      </p>
    </div>

    <!-- Action -->
    <div class="flex items-center justify-between mt-auto pt-6 border-t border-gray-50 z-10">
      <span class="text-[10px] font-bold uppercase tracking-widest text-gray-400 group-hover:text-gray-900 transition-colors">
        查看详情
      </span>
      <div class="w-10 h-10 rounded-full bg-gray-50 flex items-center justify-center group-hover:bg-gray-900 group-hover:text-white transition-all shadow-sm">
        <FontAwesomeIcon icon="fa-solid fa-arrow-right" class="text-sm" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ModuleConfig } from '../types';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';

defineProps<{
  module: ModuleConfig;
  index: number;
}>();

defineEmits(['click']);
</script>

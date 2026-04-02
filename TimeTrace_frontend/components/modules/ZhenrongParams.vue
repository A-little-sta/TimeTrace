<script setup lang="ts">
import { ref, computed } from 'vue';

// 定义属性
const props = defineProps<{
  params: {
    faceEnhanceLevel: number;
    skinSmooth: number;
    eyeEnhance: boolean;
    lipEnhance: boolean;
  };
}>();

// 定义事件
const emit = defineEmits<{
  (e: 'update:params', value: typeof props.params): void;
}>();

// 计算属性，用于双向绑定
const localParams = computed({
  get: () => props.params,
  set: (value) => emit('update:params', value)
});
</script>

<template>
  <div class="bg-white p-6 rounded-3xl shadow-sm border border-gray-100">
    <h3 class="text-lg font-medium text-gray-800 mb-4">真容修复参数设置</h3>
    
    <!-- 面部增强程度 -->
    <div class="mb-4">
      <label class="block text-sm font-medium text-gray-600 mb-2">面部增强程度</label>
      <div class="flex items-center gap-3">
        <input
          type="range"
          min="1"
          max="10"
          step="1"
          v-model.number="localParams.faceEnhanceLevel"
          class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-400"
        />
        <span class="text-sm text-gray-600 min-w-[30px]">{{ localParams.faceEnhanceLevel }}</span>
      </div>
      <p class="text-xs text-gray-500 mt-1">控制面部整体增强的强度，值越高效果越明显</p>
    </div>
    
    <!-- 皮肤平滑度 -->
    <div class="mb-4">
      <label class="block text-sm font-medium text-gray-600 mb-2">皮肤平滑度</label>
      <div class="flex items-center gap-3">
        <input
          type="range"
          min="0"
          max="100"
          step="5"
          v-model.number="localParams.skinSmooth"
          class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-400"
        />
        <span class="text-sm text-gray-600 min-w-[40px]">{{ localParams.skinSmooth }}%</span>
      </div>
      <p class="text-xs text-gray-500 mt-1">平滑皮肤纹理，减少皱纹和瑕疵</p>
    </div>
    
    <!-- 眼部增强 -->
    <div class="mb-4">
      <label class="block text-sm font-medium text-gray-600 mb-2">眼部增强</label>
      <div class="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          v-model="localParams.eyeEnhance"
          class="w-4 h-4 rounded accent-primary-400"
        />
        <span class="text-sm text-gray-700">增强眼部细节</span>
      </div>
      <p class="text-xs text-gray-500 mt-1">增强眼睛的清晰度和细节，使眼睛更加有神</p>
    </div>
    
    <!-- 唇部增强 -->
    <div>
      <label class="block text-sm font-medium text-gray-600 mb-2">唇部增强</label>
      <div class="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          v-model="localParams.lipEnhance"
          class="w-4 h-4 rounded accent-primary-400"
        />
        <span class="text-sm text-gray-700">增强唇部细节</span>
      </div>
      <p class="text-xs text-gray-500 mt-1">增强唇部的色彩和细节，使嘴唇更加自然饱满</p>
    </div>
  </div>
</template>

<style scoped>
/* 组件特定样式 */
</style>

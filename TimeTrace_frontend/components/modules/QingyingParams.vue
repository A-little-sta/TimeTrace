<script setup lang="ts">
import { ref, computed } from 'vue';

// 定义属性
const props = defineProps<{
  params: {
    prompt: string;
    upscale: number;
    patchSize: number;
    stride: number;
    seed: number;
    enhanceText: boolean;
    repairBackground: boolean;
  };
}>();

// 定义事件
const emit = defineEmits<{
  (e: 'update:params', value: typeof props.params): void;
  (e: 'recognize-text'): void;
}>();

// 计算属性，用于双向绑定
const localParams = computed({
  get: () => props.params,
  set: (value) => emit('update:params', value)
});

// 处理文本识别请求
const handleRecognizeText = () => {
  emit('recognize-text');
};

// 生成随机种子
const generateRandomSeed = () => {
  // 生成0到2^32-1之间的随机数
  return Math.floor(Math.random() * 4294967296);
};
</script>

<template>
  <div class="bg-white p-6 rounded-3xl shadow-sm border border-gray-100">
    <h3 class="text-lg font-medium text-gray-800 mb-4">清影修复参数设置</h3>
    
    <!-- 文本提示 -->
    <div class="mb-4">
      <div class="flex items-center justify-between mb-2">
        <label class="block text-sm font-medium text-gray-600">修复提示词</label>
        <button
          @click="handleRecognizeText"
          class="text-xs bg-primary-100 text-primary-700 px-3 py-1 rounded-full hover:bg-primary-200 transition-colors"
        >
          识别图像文字
        </button>
      </div>
      <textarea
        v-model="localParams.prompt"
        class="w-full h-20 p-3 border border-gray-200 rounded-xl resize-y focus:outline-none focus:ring-2 focus:ring-primary-400"
        placeholder="输入描述修复需求的提示词，例如：'清晰修复老照片，增强细节，修复背景'"
      ></textarea>
      <p class="text-xs text-gray-500 mt-1">详细的提示词可以获得更精确的修复效果</p>
    </div>
    
    <!-- 功能选项 -->
    <div class="mb-4">
      <label class="block text-sm font-medium text-gray-600 mb-2">功能选项</label>
      <div class="space-y-2">
        <label class="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            v-model="localParams.enhanceText"
            class="w-4 h-4 rounded accent-primary-400"
          />
          <span class="text-sm text-gray-700">增强文字清晰度</span>
        </label>
        <label class="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            v-model="localParams.repairBackground"
            class="w-4 h-4 rounded accent-primary-400"
          />
          <span class="text-sm text-gray-700">修复背景细节</span>
        </label>
      </div>
    </div>
    
    <!-- 放大倍数 -->
    <div class="mb-4">
      <label class="block text-sm font-medium text-gray-600 mb-2">放大倍数</label>
      <select
        v-model="localParams.upscale"
        class="w-full p-2 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-400"
      >
        <option value="1">1x (保持原尺寸)</option>
        <option value="2">2x (放大2倍)</option>
        <option value="4">4x (放大4倍)</option>
        <option value="8">8x (放大8倍)</option>
      </select>
    </div>
    
    <!-- 高级参数 -->
    <div class="mb-4">
      <details class="group">
        <summary class="flex items-center justify-between cursor-pointer py-2 text-sm font-medium text-gray-600">
          <span>高级参数</span>
          <svg class="w-4 h-4 transition-transform group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
          </svg>
        </summary>
        <div class="pt-2 space-y-4">
          <!-- Patch大小 -->
          <div>
            <label class="block text-xs font-medium text-gray-600 mb-1">Patch大小</label>
            <select
              v-model="localParams.patchSize"
              class="w-full p-2 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-400"
            >
              <option value="512">512px</option>
              <option value="640">640px</option>
              <option value="768">768px</option>
              <option value="896">896px</option>
              <option value="1024">1024px</option>
            </select>
            <p class="text-xs text-gray-500 mt-1">控制修复时的处理块大小，值越大处理越慢但效果可能更好</p>
          </div>
          
          <!-- Stride -->
          <div>
            <label class="block text-xs font-medium text-gray-600 mb-1">Stride</label>
            <select
              v-model="localParams.stride"
              class="w-full p-2 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-400"
            >
              <option value="256">256px</option>
              <option value="320">320px</option>
              <option value="384">384px</option>
              <option value="448">448px</option>
              <option value="512">512px</option>
            </select>
            <p class="text-xs text-gray-500 mt-1">控制处理块的重叠程度，值越小重叠越多处理越慢但效果可能更好</p>
          </div>
          
          <!-- 随机种子 -->
          <div>
            <label class="block text-xs font-medium text-gray-600 mb-1">随机种子</label>
            <div class="flex items-center gap-2">
              <input
                type="number"
                v-model="localParams.seed"
                class="flex-1 p-2 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-400"
              />
              <button
                @click="localParams.seed = generateRandomSeed()"
                class="text-xs bg-gray-100 text-gray-700 px-3 py-2 rounded-xl hover:bg-gray-200 transition-colors"
              >
                随机
              </button>
            </div>
            <p class="text-xs text-gray-500 mt-1">使用相同种子可以获得一致的结果，点击随机按钮生成随机数</p>
          </div>
        </div>
      </details>
    </div>
  </div>
</template>

<style scoped>
/* 组件特定样式 */
</style>

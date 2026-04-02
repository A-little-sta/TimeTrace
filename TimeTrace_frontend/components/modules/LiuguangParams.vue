<template>
  <div class="bg-white/90 backdrop-blur-md p-6 rounded-[1.5rem] shadow-xl border border-amber-100/50 space-y-8 relative overflow-hidden">
    
    <!-- 装饰背景 -->
    <div class="absolute -top-10 -right-10 w-32 h-32 bg-amber-200/20 rounded-full blur-3xl pointer-events-none"></div>
    <div class="absolute bottom-0 left-0 w-24 h-24 bg-yellow-100/30 rounded-full blur-2xl pointer-events-none"></div>

    <!-- 标题栏 -->
    <div class="flex items-center gap-3 border-b border-amber-100 pb-4 relative z-10">
      <div class="w-10 h-10 rounded-full bg-gradient-to-br from-amber-100 to-amber-50 flex items-center justify-center text-amber-600 shadow-sm border border-amber-100">
        <i class="fa-solid fa-wand-magic-sparkles text-lg"></i>
      </div>
      <div>
        <h3 class="text-lg font-bold text-gray-800 tracking-wide">流光 · 智能上色</h3>
        <p class="text-xs text-amber-600/80 font-medium">Smart AI Colorization</p>
      </div>
    </div>

    <div class="relative z-10 space-y-6">
      
      <!-- 实时预览区域 -->
      <div v-if="showPreview" class="bg-gradient-to-br from-amber-50 to-yellow-50 rounded-xl p-4 border border-amber-200">
        <div class="flex items-center justify-between mb-3">
          <label class="text-sm font-bold text-gray-700 flex items-center gap-2">
            <i class="fa-solid fa-eye text-amber-500"></i>
            实时预览
          </label>
          <button 
            @click="togglePreview"
            class="text-xs text-amber-600 bg-amber-100 px-2 py-1 rounded-full hover:bg-amber-200 transition-colors"
          >
            {{ isPreviewActive ? '隐藏预览' : '显示预览' }}
          </button>
        </div>
        
        <div v-if="isPreviewActive" class="grid grid-cols-2 gap-4">
          <div class="text-center">
            <div class="text-xs text-gray-500 mb-1">原图</div>
            <div class="bg-gray-100 rounded-lg p-2 border border-gray-200">
              <img :src="originalImageUrl" class="w-full h-24 object-cover rounded" v-if="originalImageUrl" />
              <div v-else class="h-24 flex items-center justify-center text-gray-400">
                <i class="fa-solid fa-image text-2xl"></i>
              </div>
            </div>
          </div>
          <div class="text-center">
            <div class="text-xs text-gray-500 mb-1">预览效果</div>
            <div class="bg-amber-50 rounded-lg p-2 border border-amber-200 relative">
              <img :src="previewImageUrl" class="w-full h-24 object-cover rounded" v-if="previewImageUrl" />
              <div v-else class="h-24 flex items-center justify-center text-amber-400">
                <i class="fa-solid fa-spinner animate-spin text-2xl"></i>
              </div>
              <div v-if="isGeneratingPreview" class="absolute inset-0 bg-black/20 rounded flex items-center justify-center">
                <i class="fa-solid fa-spinner animate-spin text-white text-lg"></i>
              </div>
            </div>
          </div>
        </div>
        
        <div v-if="isPreviewActive" class="mt-3 flex gap-2">
          <button 
            @click="generatePreview"
            :disabled="isGeneratingPreview"
            class="flex-1 bg-primary-500 text-white py-2 rounded-lg text-sm font-medium hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <i class="fa-solid fa-rotate mr-1"></i>
            刷新预览
          </button>
          <button 
            @click="savePreview"
            :disabled="!previewImageUrl"
            class="flex-1 bg-primary-500 text-white py-2 rounded-lg text-sm font-medium hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <i class="fa-solid fa-download mr-1"></i>
            保存优化
          </button>
        </div>
      </div>

      <!-- 1. 多模态提示词 -->
      <div>
        <label class="text-sm font-bold text-gray-700 mb-2 flex items-center gap-2">
          <i class="fa-solid fa-keyboard text-amber-500"></i>
          文本指导 (可选)
        </label>
        <div class="relative group">
          <input 
            type="text" 
            v-model="localParams.prompt"
            placeholder="例如: '日落', '森林', '复古街景'..."
            class="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-amber-200 focus:border-amber-400 outline-none transition-all placeholder-gray-400"
            @input="onPromptChange"
          />
          <div class="absolute right-3 top-3 text-xs text-gray-400 bg-gray-100 px-2 rounded">AI 辅助</div>
        </div>
      </div>

      <!-- 2. 色调调节 -->
      <div class="space-y-4">
        <label class="text-sm font-bold text-gray-700 flex items-center gap-2">
          <i class="fa-solid fa-sliders text-amber-500"></i>
          色彩微调
        </label>
        
        <!-- 色温滑块 -->
        <div class="bg-gray-50 p-3 rounded-xl border border-gray-100">
          <div class="flex justify-between text-xs text-gray-500 mb-1">
            <span>❄️ 冷色调</span>
            <span class="font-bold text-gray-700">色温 (Warmth)</span>
            <span>🔥 暖色调</span>
          </div>
          <input 
            type="range" 
            v-model.number="localParams.warmth" 
            min="-1.0" max="1.0" step="0.1"
            class="w-full h-2 bg-gradient-to-r from-blue-200 via-gray-200 to-orange-200 rounded-lg appearance-none cursor-pointer accent-amber-500"
            @input="onColorChange"
          >
          <div class="text-xs text-gray-400 text-center mt-1">
            当前: {{ localParams.warmth }}
          </div>
        </div>

        <!-- 鲜艳度滑块 -->
        <div class="bg-gray-50 p-3 rounded-xl border border-gray-100">
          <div class="flex justify-between text-xs text-gray-500 mb-1">
            <span>⚪ 淡雅</span>
            <span class="font-bold text-gray-700">鲜艳度 (Saturation)</span>
            <span>🌈 浓郁</span>
          </div>
          <input 
            type="range" 
            v-model.number="localParams.saturation" 
            min="0.5" max="1.5" step="0.1"
            class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-amber-500"
            @input="onColorChange"
          >
          <div class="text-xs text-gray-400 text-center mt-1">
            当前: {{ localParams.saturation }}
          </div>
        </div>

        <!-- 对比度滑块 -->
        <div class="bg-gray-50 p-3 rounded-xl border border-gray-100">
          <div class="flex justify-between text-xs text-gray-500 mb-1">
            <span>🌫️ 柔和</span>
            <span class="font-bold text-gray-700">对比度 (Contrast)</span>
            <span>✨ 鲜明</span>
          </div>
          <input 
            type="range" 
            v-model.number="localParams.contrast" 
            min="0.5" max="2.0" step="0.1"
            class="w-full h-2 bg-gradient-to-r from-gray-200 via-gray-300 to-gray-400 rounded-lg appearance-none cursor-pointer accent-amber-500"
            @input="onColorChange"
          >
          <div class="text-xs text-gray-400 text-center mt-1">
            当前: {{ localParams.contrast }}
          </div>
        </div>
      </div>

      <!-- 3. 高级选项 -->
      <div class="bg-gray-50/80 rounded-xl p-4 border border-gray-100">
        <label class="text-sm font-medium text-gray-700 flex items-center gap-2 cursor-pointer">
          <input 
            type="checkbox" 
            v-model="localParams.colorEnhance"
            class="w-4 h-4 text-amber-500 border-gray-300 rounded focus:ring-amber-400"
          >
          <span>智能光影增强 (Auto Enhance)</span>
        </label>
        <p class="text-xs text-gray-400 mt-2 pl-6">
          自动修复过暗或对比度不足的问题 (Zero-DCE/CLAHE)。
        </p>
      </div>

      <!-- 预设方案 -->
      <div class="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-4 border border-blue-200">
        <label class="text-sm font-bold text-gray-700 mb-3 flex items-center gap-2">
          <i class="fa-solid fa-palette text-blue-500"></i>
          快速预设
        </label>
        <div class="grid grid-cols-3 gap-2">
          <button 
            v-for="preset in colorPresets" 
            :key="preset.name"
            @click="applyPreset(preset)"
            class="py-2 px-3 rounded-lg text-xs font-medium transition-all hover:scale-105 active:scale-95"
            :class="preset.class"
          >
            {{ preset.name }}
          </button>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';

/**
 * 流光修复参数组件
 * 负责管理图像上色和色彩增强相关的参数配置
 * 支持多模态提示词指导、实时预览、色彩微调等功能
 */

const props = defineProps<{
  params: {
    modelSize: string;
    model?: string;
    inputSize: number;
    colorEnhance: boolean;
    prompt?: string;
    warmth?: number;     // 新增
    saturation?: number; // 新增
    contrast?: number;   // 新增
    [key: string]: any;
  };
  isVideoProp?: boolean;
  originalImageUrl?: string; // 新增：原图URL
}>();

const emit = defineEmits(['update:params', 'preview', 'save']);

// 响应式数据
const isPreviewActive = ref(false);
const isGeneratingPreview = ref(false);
const previewImageUrl = ref('');
const previewDebounce = ref<NodeJS.Timeout | null>(null);

// 计算属性：双向绑定 params，并初始化默认值
const localParams = computed({
  get: () => props.params,
  set: (value) => {
    value.model = value.modelSize; // 兼容旧逻辑
    
    // 初始化新参数默认值
    if (value.prompt === undefined) value.prompt = '';
    if (value.warmth === undefined) value.warmth = 0.0; // 0.0 是中性
    if (value.saturation === undefined) value.saturation = 1.0; // 1.0 是原色
    if (value.contrast === undefined) value.contrast = 1.0; // 1.0 是原色
    
    emit('update:params', value);
  }
});

// 计算是否显示预览区域
const showPreview = computed(() => {
  return props.originalImageUrl && !props.isVideoProp;
});

// 颜色预设方案
const colorPresets = ref([
  { name: '自然', warmth: 0.0, saturation: 1.0, contrast: 1.0, class: 'bg-gray-100 text-gray-700 hover:bg-gray-200' },
  { name: '鲜艳', warmth: 0.2, saturation: 1.3, contrast: 1.1, class: 'bg-red-100 text-red-700 hover:bg-red-200' },
  { name: '温暖', warmth: 0.6, saturation: 1.2, contrast: 1.0, class: 'bg-orange-100 text-orange-700 hover:bg-orange-200' },
  { name: '冷调', warmth: -0.4, saturation: 0.9, contrast: 1.1, class: 'bg-blue-100 text-blue-700 hover:bg-blue-200' },
  { name: '复古', warmth: 0.3, saturation: 0.8, contrast: 1.2, class: 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200' },
  { name: '电影', warmth: 0.1, saturation: 1.1, contrast: 1.3, class: 'bg-purple-100 text-purple-700 hover:bg-purple-200' }
]);

// 方法
const togglePreview = () => {
  isPreviewActive.value = !isPreviewActive.value;
  if (isPreviewActive.value && props.originalImageUrl) {
    generatePreview();
  }
};

const onPromptChange = () => {
  // 提示词变化时延迟生成预览
  if (isPreviewActive.value) {
    schedulePreview();
  }
};

const onColorChange = () => {
  // 颜色参数变化时实时生成预览
  if (isPreviewActive.value) {
    schedulePreview();
  }
};

const schedulePreview = () => {
  // 防抖处理，避免频繁请求
  if (previewDebounce.value) {
    clearTimeout(previewDebounce.value);
  }
  previewDebounce.value = setTimeout(() => {
    generatePreview();
  }, 500);
};

const generatePreview = async () => {
  if (!props.originalImageUrl || isGeneratingPreview.value) return;
  
  isGeneratingPreview.value = true;
  
  try {
    // 模拟预览生成（实际项目中需要调用后端API）
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // 这里应该调用后端API生成预览
    // const response = await fetch('/api/liuguang/preview', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify({
    //     imageUrl: props.originalImageUrl,
    //     warmth: localParams.value.warmth,
    //     saturation: localParams.value.saturation,
    //     contrast: localParams.value.contrast,
    //     prompt: localParams.value.prompt
    //   })
    // });
    // const data = await response.json();
    // previewImageUrl.value = data.previewUrl;
    
    // 临时使用原图作为预览（实际项目中需要替换为真实预览URL）
    previewImageUrl.value = props.originalImageUrl + '?preview=' + Date.now();
    
    // 发送预览事件给父组件
    emit('preview', {
      imageUrl: previewImageUrl.value,
      params: { ...localParams.value }
    });
    
  } catch (error) {
    console.error('生成预览失败:', error);
  } finally {
    isGeneratingPreview.value = false;
  }
};

const savePreview = () => {
  if (!previewImageUrl.value) return;
  
  // 发送保存事件给父组件
  emit('save', {
    imageUrl: previewImageUrl.value,
    params: { ...localParams.value }
  });
};

const applyPreset = (preset: any) => {
  const newParams = { ...localParams.value };
  newParams.warmth = preset.warmth;
  newParams.saturation = preset.saturation;
  newParams.contrast = preset.contrast;
  
  emit('update:params', newParams);
  
  // 应用预设后立即生成预览
  if (isPreviewActive.value) {
    generatePreview();
  }
};



const selectModelType = (type: string) => {
  const newParams = { ...localParams.value };
  newParams.modelSize = type;
  newParams.model = type;
  emit('update:params', newParams);
};

// 监听原图URL变化
watch(() => props.originalImageUrl, (newUrl) => {
  if (newUrl && isPreviewActive.value) {
    generatePreview();
  }
});

// 组件挂载时初始化
if (props.originalImageUrl && !props.isVideoProp) {
  // 延迟显示预览，让用户先看到界面
  setTimeout(() => {
    isPreviewActive.value = true;
    generatePreview();
  }, 1000);
}
</script>
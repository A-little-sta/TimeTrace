<script setup lang="ts">
import { ref, computed, watch } from 'vue';

// 定义属性
const props = defineProps<{
  params: {
    detectThreshold: number;
    dilateLevel: number;
  };
  repairMode: 'auto' | 'manual' | 'denoise';
}>();

// 定义事件
const emit = defineEmits<{
  (e: 'update:params', value: typeof props.params): void;
  (e: 'update:repairMode', value: 'auto' | 'manual' | 'denoise'): void;
}>();

// 计算属性，用于双向绑定
const localParams = computed({
  get: () => props.params,
  set: (value) => emit('update:params', value)
});

const localRepairMode = computed({
  get: () => props.repairMode,
  set: (value) => emit('update:repairMode', value)
});

// 模型配置数据 - 仅使用Lama模型
const modelConfig = {
  lama: {
    name: "Lama修复模型",
    displayName: "拂尘修复-Lama版",
    description: "Lama模型，专业的图像修复模型，适合各种划痕修复和图像补全任务",
    advantages: [
      "修复效果优秀，质量高",
      "适合各种复杂修复场景",
      "稳定性好，可靠性高"
    ],
    limitations: [
      "处理速度适中",
      "对硬件有一定要求",
      "需要GPU支持以获得最佳性能"
    ],
    bestFor: "专业照片修复、高质量图像处理"
  }
};

// 初始化时设置默认值
const initializeDefaults = () => {
  // 设置默认参数值
  if (!localParams.value.detectThreshold) {
    localParams.value.detectThreshold = 0.5;
  }
  if (!localParams.value.dilateLevel) {
    localParams.value.dilateLevel = 3;
  }
};

// 组件挂载时初始化默认值
initializeDefaults();
</script>

<template>
  <div class="bg-white p-6 rounded-3xl shadow-sm border border-gray-100">
    <h3 class="text-lg font-medium text-gray-800 mb-4">拂尘修复参数设置</h3>
    
    <!-- 修复模式选择 -->
    <div class="mb-6">
      <label class="block text-sm font-medium text-gray-600 mb-3">修复模式</label>
      <div class="grid grid-cols-3 gap-3">
        <!-- 自动修复 -->
        <label 
          class="flex flex-col p-4 border-2 rounded-xl cursor-pointer transition-all hover:border-primary-300"
          :class="localRepairMode === 'auto' 
            ? 'border-primary-400 bg-primary-50' 
            : 'border-gray-200 bg-white'"
        >
          <div class="flex items-center gap-2 mb-2">
            <input
              type="radio"
              value="auto"
              v-model="localRepairMode"
              class="accent-primary-400"
            />
            <span class="text-sm font-medium text-gray-700">自动修复</span>
          </div>
          <span class="text-xs text-gray-500">系统智能检测并修复疤痕、划痕等瑕疵</span>
        </label>
        
        <!-- 手动修复 -->
        <label 
          class="flex flex-col p-4 border-2 rounded-xl cursor-pointer transition-all hover:border-primary-300"
          :class="localRepairMode === 'manual' 
            ? 'border-primary-400 bg-primary-50' 
            : 'border-gray-200 bg-white'"
        >
          <div class="flex items-center gap-2 mb-2">
            <input
              type="radio"
              value="manual"
              v-model="localRepairMode"
              class="accent-primary-400"
            />
            <span class="text-sm font-medium text-gray-700">手动修复</span>
          </div>
          <span class="text-xs text-gray-500">手动涂抹需要修复的区域，适合复杂疤痕</span>
        </label>
        
        <!-- 降噪修复 -->
        <label 
          class="flex flex-col p-4 border-2 rounded-xl cursor-pointer transition-all hover:border-blue-300"
          :class="localRepairMode === 'denoise' 
            ? 'border-blue-400 bg-blue-50' 
            : 'border-gray-200 bg-white'"
        >
          <div class="flex items-center gap-2 mb-2">
            <input
              type="radio"
              value="denoise"
              v-model="localRepairMode"
              class="accent-blue-400"
            />
            <span class="text-sm font-medium text-gray-700">降噪修复</span>
          </div>
          <span class="text-xs text-gray-500">去除照片中的摩尔纹、噪点和图像噪声</span>
        </label>
      </div>
    </div>
    
    <!-- 模型信息显示 -->
    <div class="mb-4 p-4 bg-white rounded-xl border border-gray-200 shadow-sm">
      <div class="flex items-center gap-2 mb-4">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5 text-purple-600">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 0 1-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 0 1 4.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0 1 12 15a9.065 9.065 0 0 1-6.23-1.307L4.2 15.3m15.6 0c.193-.205.293-.438.293-.713 0-.275-.1-.508-.293-.713m0 0a.75.75 0 0 0-.564-.439l-3.098-.826a.75.75 0 0 0-.534.039l-.894.298a.75.75 0 0 1-.99-.464l-.712-2.13a.75.75 0 0 0-.464-.464l-2.13-.712a.75.75 0 0 1-.464-.99l.298-.894a.75.75 0 0 0 .04-.534l-.826-3.098a.75.75 0 0 0-.44-.564M4.2 15.3a.75.75 0 0 0 .293.713c.205.193.438.293.713.293.275 0 .508-.1.713-.293m0 0L9 10.5" />
        </svg>
        <h4 class="text-sm font-medium text-gray-800">AI模型信息</h4>
      </div>
      
      <!-- 模型详细信息 -->
      <div class="bg-gray-50 p-3 rounded-lg border border-gray-200">
        <div class="flex items-center justify-between mb-2">
          <span class="text-sm font-medium text-gray-700">{{ modelConfig.lama.name }}</span>
          <span class="text-xs px-2 py-1 bg-purple-100 text-purple-600 rounded-full">LAMA</span>
        </div>
        <p class="text-xs text-gray-600 mb-2">{{ modelConfig.lama.description }}</p>
        
        <div class="grid grid-cols-2 gap-2 text-xs">
          <div>
            <span class="font-medium text-green-600">优势：</span>
            <ul class="list-disc list-inside text-gray-500">
              <li v-for="advantage in modelConfig.lama.advantages.slice(0, 2)" :key="advantage">{{ advantage }}</li>
            </ul>
          </div>
          <div>
            <span class="font-medium text-orange-600">注意：</span>
            <ul class="list-disc list-inside text-gray-500">
              <li v-for="limitation in modelConfig.lama.limitations.slice(0, 2)" :key="limitation">{{ limitation }}</li>
            </ul>
          </div>
        </div>
        
        <div class="mt-2 p-2 bg-blue-50 rounded border border-blue-100">
          <span class="text-xs font-medium text-blue-600">最适合：</span>
          <span class="text-xs text-blue-600">{{ modelConfig.lama.bestFor }}</span>
        </div>
      </div>
    </div>

    <!-- 疤痕修复参数设置（仅限疤痕修复模式） -->
    <div v-if="localRepairMode !== 'denoise'" class="mb-4 p-4 bg-white rounded-xl border border-gray-200 shadow-sm">
      <div class="flex items-center gap-2 mb-4">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5 text-blue-600">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0-3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0-3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0-2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0-2.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 0 0-2.456 2.456ZM16.894 20.567 16.5 21.75l-.394-1.183a2.25 2.25 0 0 0-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 0 0-1.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 0 0-1.423 1.423l1.183.394-1.183.394a2.25 2.25 0 0 0-1.423 1.423Z" />
        </svg>
        <h4 class="text-sm font-medium text-gray-800">修复参数设置</h4>
      </div>
      
      <!-- 检测灵敏度 -->
      <div class="mb-4">
        <div class="flex items-center justify-between mb-2">
          <label class="text-sm font-medium text-gray-700">检测灵敏度</label>
          <span class="text-xs font-mono bg-gray-100 px-2 py-1 rounded text-gray-600">{{ localParams.detectThreshold }}</span>
        </div>
        <input 
          type="range" 
          v-model="localParams.detectThreshold" 
          min="0.1" 
          max="0.9" 
          step="0.1"
          class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider-blue"
        >
        <div class="flex justify-between text-xs text-gray-500 mt-1">
          <span>宽松检测</span>
          <span>适中</span>
          <span>严格检测</span>
        </div>
        <p class="text-xs text-gray-500 mt-1">控制疤痕检测的严格程度，建议使用默认值</p>
      </div>
      
      <!-- 修复范围 -->
      <div class="mb-2">
        <div class="flex items-center justify-between mb-2">
          <label class="text-sm font-medium text-gray-700">修复范围</label>
          <span class="text-xs font-mono bg-gray-100 px-2 py-1 rounded text-gray-600">{{ localParams.dilateLevel }}</span>
        </div>
        <input 
          type="range" 
          v-model="localParams.dilateLevel" 
          min="1" 
          max="10" 
          step="1"
          class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider-blue"
        >
        <div class="flex justify-between text-xs text-gray-500 mt-1">
          <span>精确修复</span>
          <span>适中</span>
          <span>扩展修复</span>
        </div>
        <p class="text-xs text-gray-500 mt-1">控制修复区域的扩展程度，建议使用默认值</p>
      </div>
      
      <!-- 默认值提示 -->
      <div class="mt-3 p-2 bg-blue-50 rounded-lg border border-blue-100">
        <div class="flex items-center gap-1">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4 text-blue-600">
            <path stroke-linecap="round" stroke-linejoin="round" d="m11.25 11.25.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z" />
          </svg>
          <span class="text-xs text-blue-600">推荐使用默认参数，系统已优化至最佳效果</span>
        </div>
      </div>
    </div>
    
    <!-- UHDM降噪修复设置（仅限降噪修复模式） -->
    <div v-if="localRepairMode === 'denoise'" class="mb-4 p-4 bg-blue-50 rounded-xl border border-blue-200">
      <div class="flex items-center gap-2 mb-3">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5 text-blue-600">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0-2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0-2.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 0 0-2.456 2.456ZM16.894 20.567 16.5 21.75l-.394-1.183a2.25 2.25 0 0 0-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 0 0-1.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 0 0-1.423 1.423l1.183.394-1.183.394a2.25 2.25 0 0 0-1.423 1.423Z" />
        </svg>
        <h4 class="text-sm font-medium text-blue-800">UHDM 降噪修复</h4>
      </div>
      
      <div class="mb-3">
        <div class="flex items-center gap-2 p-2 bg-blue-100 rounded-lg">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4 text-blue-600">
            <path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
          </svg>
          <span class="text-sm text-blue-700 font-medium">已启用 UHDM 降噪算法</span>
        </div>
        <p class="text-xs text-blue-600 mt-1">专门用于去除图像中的摩尔纹、噪点和图像噪声</p>
      </div>
      
      <div class="mb-2">
        <div class="flex items-center gap-2 mb-1">
          <span class="text-sm font-medium text-gray-600">算法类型：</span>
          <span class="text-sm font-medium text-blue-600">Ultra-High-Definition Image Demoiréing</span>
        </div>
        <p class="text-xs text-gray-500">高级降噪算法，保持图像细节的同时去除噪声</p>
      </div>
    </div>
    
    <!-- 修复参数调整（仅限疤痕修复模式） -->
    <div v-if="localRepairMode !== 'denoise'" class="space-y-4">
      <!-- 检测灵敏度 -->
      <div>
        <label class="block text-sm font-medium text-gray-600 mb-2">
          检测灵敏度
          <span class="text-xs text-gray-400 ml-1">{{ localParams.detectThreshold }}%</span>
        </label>
        <input
          type="range"
          v-model="localParams.detectThreshold"
          min="30"
          max="90"
          step="5"
          class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
        />
        <div class="flex justify-between text-xs text-gray-500 mt-1">
          <span>低</span>
          <span>中</span>
          <span>高</span>
        </div>
      </div>
      
      <!-- 修复范围 -->
      <div>
        <label class="block text-sm font-medium text-gray-600 mb-2">
          修复范围
          <span class="text-xs text-gray-400 ml-1">{{ localParams.dilateLevel }}px</span>
        </label>
        <input
          type="range"
          v-model="localParams.dilateLevel"
          min="1"
          max="20"
          step="1"
          class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
        />
        <div class="flex justify-between text-xs text-gray-500 mt-1">
          <span>精确</span>
          <span>适中</span>
          <span>扩展</span>
        </div>
      </div>
    </div>
    
    <!-- 使用说明 -->
    <div class="mt-6 p-3 bg-blue-50 rounded-lg border border-blue-200">
      <h4 class="text-sm font-medium text-blue-800 mb-2">使用说明</h4>
      <ul class="text-xs text-blue-700 space-y-1">
        <li v-if="localRepairMode !== 'denoise'">• <strong>自动修复</strong>：系统智能检测疤痕并自动修复</li>
        <li v-if="localRepairMode !== 'denoise'">• <strong>手动修复</strong>：手动涂抹需要修复的疤痕区域</li>
        <li v-if="localRepairMode === 'denoise'">• <strong>降噪修复</strong>：去除摩尔纹、噪点和图像噪声</li>
        <li v-if="localRepairMode !== 'denoise'">• 使用官方推荐的 PowerPaint V2 模型，修复效果最佳</li>
        <li v-if="localRepairMode === 'denoise'">• 使用 UHDM 算法，专业降噪保持细节</li>
        <li>• 修复完成后可查看对比效果</li>
        <li>• <strong>继续修复功能</strong>：修复完成后点击"继续修复"按钮，可将当前修复结果作为新的输入进行进一步修复</li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.slider::-webkit-slider-thumb {
  appearance: none;
  height: 16px;
  width: 16px;
  border-radius: 50%;
  background: #3b82f6;
  cursor: pointer;
}

.slider::-moz-range-thumb {
  height: 16px;
  width: 16px;
  border-radius: 50%;
  background: #3b82f6;
  cursor: pointer;
  border: none;
}
</style>
<script setup lang="ts">
import { computed } from 'vue';

export interface DimensionSculptorParamsType {
  mode: 'draft' | 'refine';
  autoTexture: boolean;
}

const props = defineProps<{
  params: DimensionSculptorParamsType;
}>();

const emit = defineEmits<{
  (e: 'update:params', value: DimensionSculptorParamsType): void;
}>();

const localParams = computed({
  get: () => props.params,
  set: (value) => emit('update:params', value),
});
</script>

<template>
  <div class="bg-white p-6 rounded-3xl shadow-sm border border-gray-100">
    <h3 class="text-lg font-medium text-gray-800 mb-4">维度重塑参数设置</h3>

    <!-- 重塑精度选择 -->
    <div class="mb-6">
      <label class="block text-sm font-medium text-gray-600 mb-3">重塑精度</label>
      <div class="grid grid-cols-2 gap-3">
        <label
          class="flex flex-col p-4 border-2 rounded-xl cursor-pointer transition-all hover:border-primary-300"
          :class="localParams.mode === 'draft'
            ? 'border-primary-400 bg-primary-50'
            : 'border-gray-200 bg-white'"
        >
          <div class="flex items-center gap-2 mb-2">
            <input
              type="radio"
              value="draft"
              v-model="localParams.mode"
              class="accent-primary-400"
            />
            <span class="text-sm font-medium text-gray-700">极速草模</span>
          </div>
          <span class="text-xs text-gray-500">约需 10 秒，快速预览3D结构</span>
        </label>

        <label
          class="flex flex-col p-4 border-2 rounded-xl cursor-pointer transition-all hover:border-amber-300"
          :class="localParams.mode === 'refine'
            ? 'border-amber-400 bg-amber-50'
            : 'border-gray-200 bg-white'"
        >
          <div class="flex items-center gap-2 mb-2">
            <input
              type="radio"
              value="refine"
              v-model="localParams.mode"
              class="accent-amber-400"
            />
            <span class="text-sm font-medium text-gray-700">极致精修</span>
          </div>
          <span class="text-xs text-gray-500">约需 2 分钟，包含拓扑优化</span>
        </label>
      </div>
    </div>

    <!-- PBR纹理映射开关 -->
    <div class="mb-6 p-4 bg-amber-50/50 rounded-xl border border-amber-100">
      <div class="flex items-center justify-between">
        <div class="flex-1">
          <label class="text-sm font-medium text-gray-700">智能PBR纹理映射</label>
          <p class="text-xs text-gray-500 mt-1">生成逼真的物理渲染材质</p>
        </div>
        <button
          type="button"
          role="switch"
          :aria-checked="localParams.autoTexture"
          @click="localParams = { ...localParams, autoTexture: !localParams.autoTexture }"
          class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-amber-400 focus:ring-offset-2"
          :class="localParams.autoTexture ? 'bg-amber-500' : 'bg-gray-200'"
        >
          <span
            class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform"
            :class="localParams.autoTexture ? 'translate-x-6' : 'translate-x-1'"
          />
        </button>
      </div>
    </div>

    <!-- 引擎信息 -->
    <div class="p-4 bg-gradient-to-br from-amber-50 to-orange-50 rounded-xl border border-amber-200">
      <div class="flex items-center gap-2 mb-3">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5 text-amber-600">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21 7.5l-9-5.25L3 7.5m18 0l-9 5.25m9-5.25v9l-9 5.25M3 7.5l9 5.25M3 7.5v9l9 5.25m0-9v9" />
        </svg>
        <h4 class="text-sm font-medium text-amber-800">Tripo3D 核心引擎</h4>
      </div>
      <p class="text-xs text-amber-700 leading-relaxed">
        基于深度学习从单张照片重建3D模型，支持 glTF/GLB 格式导出。草模模式快速预览结构，精修模式进行拓扑优化与纹理增强。
      </p>
    </div>

    <!-- 使用说明 -->
    <div class="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
      <h4 class="text-sm font-medium text-blue-800 mb-2">使用说明</h4>
      <ul class="text-xs text-blue-700 space-y-1">
        <li>上传清晰的正面或3/4侧面照片效果最佳</li>
        <li>极速草模：快速生成基础3D结构预览</li>
        <li>极致精修：生成高质量3D模型，附带PBR材质</li>
        <li>生成完成后可在3D查看器中交互旋转缩放</li>
      </ul>
    </div>
  </div>
</template>
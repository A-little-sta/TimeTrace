<script setup lang="ts">
import { ref, onMounted, watch, onBeforeUnmount } from 'vue';

interface BrushCanvasProps {
  imageUrl: string;
  brushSize?: number;
  brushColor?: string;
  opacity?: number;
}

const props = withDefaults(defineProps<BrushCanvasProps>(), {
  brushSize: 10,
  brushColor: '#FF0000',
  opacity: 0.6
});

const emit = defineEmits<{
  (e: 'maskChange', maskData: string): void;
  (e: 'saveMask', maskData: string): void;
}>();

const canvasRef = ref<HTMLCanvasElement | null>(null);
const ctx = ref<CanvasRenderingContext2D | null>(null);
const isDrawing = ref(false);
const mode = ref<'draw' | 'erase'>('draw');
const imageLoaded = ref(false);
const originalImage = ref<HTMLImageElement | null>(null);
const maskCanvas = ref<HTMLCanvasElement | null>(null);
const maskCtx = ref<CanvasRenderingContext2D | null>(null);
const localBrushSize = ref(props.brushSize);

// 初始化画布
onMounted(() => {
  initCanvas();
});

onBeforeUnmount(() => {
  cleanup();
});

watch(() => props.imageUrl, () => {
  if (canvasRef.value) {
    loadImage(props.imageUrl);
  }
});

// 监听props.brushSize变化
watch(() => props.brushSize, (newSize) => {
  localBrushSize.value = newSize;
});

// 初始化画布
const initCanvas = () => {
  if (!canvasRef.value) return;
  
  ctx.value = canvasRef.value.getContext('2d');
  
  // 创建掩码画布
  maskCanvas.value = document.createElement('canvas');
  maskCtx.value = maskCanvas.value.getContext('2d');
  
  // 加载图片
  loadImage(props.imageUrl);
};

// 加载图片
const loadImage = (url: string) => {
  if (!ctx.value || !maskCtx.value) return;
  
  originalImage.value = new Image();
  originalImage.value.crossOrigin = 'anonymous';
  originalImage.value.onload = () => {
    // 设置画布尺寸
    const canvas = canvasRef.value;
    const maskCanvasEl = maskCanvas.value;
    
    if (!canvas || !maskCanvasEl) return;
    
    canvas.width = originalImage.value.width;
    canvas.height = originalImage.value.height;
    maskCanvasEl.width = originalImage.value.width;
    maskCanvasEl.height = originalImage.value.height;
    
    // 绘制原始图片
    ctx.value?.drawImage(originalImage.value, 0, 0);
    
    // 初始化掩码画布为黑色透明
    maskCtx.value.fillStyle = 'rgba(0, 0, 0, 0)';
    maskCtx.value.fillRect(0, 0, maskCanvasEl.width, maskCanvasEl.height);
    
    imageLoaded.value = true;
  };
  originalImage.value.src = url;
};

// 获取画布缩放比例
const getCanvasScale = () => {
  if (!canvasRef.value) return { scaleX: 1, scaleY: 1 };
  
  const canvas = canvasRef.value;
  const rect = canvas.getBoundingClientRect();
  
  // 计算缩放比例：实际canvas尺寸 / 显示尺寸
  const scaleX = canvas.width / rect.width;
  const scaleY = canvas.height / rect.height;
  
  return { scaleX, scaleY };
};

// 鼠标按下事件
const handleMouseDown = (e: MouseEvent) => {
  if (!imageLoaded.value || !ctx.value || !maskCtx.value) return;
  
  isDrawing.value = true;
  const rect = canvasRef.value?.getBoundingClientRect();
  if (!rect) return;
  
  // 获取缩放比例
  const { scaleX, scaleY } = getCanvasScale();
  
  // 根据缩放比例调整鼠标坐标
  const x = (e.clientX - rect.left) * scaleX;
  const y = (e.clientY - rect.top) * scaleY;
  
  // 设置绘画参数
  maskCtx.value.lineWidth = localBrushSize.value;
  maskCtx.value.lineCap = 'round';
  
  if (mode.value === 'draw') {
    maskCtx.value.globalCompositeOperation = 'source-over';
    maskCtx.value.strokeStyle = 'rgba(255, 255, 255, 1)';
  } else {
    maskCtx.value.globalCompositeOperation = 'destination-out';
    maskCtx.value.strokeStyle = 'rgba(255, 255, 255, 1)';
  }
  
  maskCtx.value.beginPath();
  maskCtx.value.moveTo(x, y);
  
  draw(x, y);
};

// 鼠标移动事件
const handleMouseMove = (e: MouseEvent) => {
  if (!isDrawing.value || !imageLoaded.value || !ctx.value || !maskCtx.value) return;
  
  const rect = canvasRef.value?.getBoundingClientRect();
  if (!rect) return;
  
  // 获取缩放比例
  const { scaleX, scaleY } = getCanvasScale();
  
  // 根据缩放比例调整鼠标坐标
  const x = (e.clientX - rect.left) * scaleX;
  const y = (e.clientY - rect.top) * scaleY;
  
  draw(x, y);
};

// 鼠标释放事件
const handleMouseUp = () => {
  isDrawing.value = false;
  updateDisplay();
  emitMaskChange();
};

// 鼠标离开画布事件
const handleMouseLeave = () => {
  isDrawing.value = false;
  updateDisplay();
  emitMaskChange();
};

// 绘制函数
const draw = (x: number, y: number) => {
  if (!maskCtx.value) return;
  
  maskCtx.value.lineTo(x, y);
  maskCtx.value.stroke();
  
  updateDisplay();
};

// 更新显示
const updateDisplay = () => {
  if (!ctx.value || !maskCtx.value || !originalImage.value) return;
  
  // 重绘原始图片
  ctx.value.drawImage(originalImage.value, 0, 0);
  
  // 设置画笔颜色和透明度
  ctx.value.globalCompositeOperation = 'source-atop';
  ctx.value.fillStyle = props.brushColor;
  ctx.value.globalAlpha = props.opacity;
  
  // 绘制掩码
  ctx.value.drawImage(maskCanvas.value!, 0, 0);
  
  // 重置合成模式
  ctx.value.globalCompositeOperation = 'source-over';
  ctx.value.globalAlpha = 1;
};

// 切换模式
const toggleMode = () => {
  mode.value = mode.value === 'draw' ? 'erase' : 'draw';
};

// 清除画布
const clearCanvas = () => {
  if (!maskCtx.value || !maskCanvas.value || !ctx.value || !originalImage.value) return;
  
  // 清除掩码画布
  maskCtx.value.fillStyle = 'rgba(0, 0, 0, 0)';
  maskCtx.value.fillRect(0, 0, maskCanvas.value.width, maskCanvas.value.height);
  
  // 重绘原始图片
  ctx.value.drawImage(originalImage.value, 0, 0);
  
  emitMaskChange();
};

// 保存掩码
const saveMask = () => {
  if (!maskCanvas.value) return;
  
  // 将掩码转换为 PNG 数据URL
  const maskData = maskCanvas.value.toDataURL('image/png');
  emit('saveMask', maskData);
};

// 发送掩码变化事件
const emitMaskChange = () => {
  if (!maskCanvas.value) return;
  
  const maskData = maskCanvas.value.toDataURL('image/png');
  emit('maskChange', maskData);
};

// 清理资源
const cleanup = () => {
  if (originalImage.value) {
    originalImage.value.onload = null;
    originalImage.value = null;
  }
  
  if (maskCanvas.value) {
    maskCanvas.value = null;
    maskCtx.value = null;
  }
};
</script>

<template>
  <div class="brush-canvas-container relative">
    <!-- 画布 -->
    <canvas
      ref="canvasRef"
      @mousedown="handleMouseDown"
      @mousemove="handleMouseMove"
      @mouseup="handleMouseUp"
      @mouseleave="handleMouseLeave"
      class="cursor-crosshair"
    ></canvas>
    
    <!-- 加载状态 -->
    <div v-if="!imageLoaded" class="absolute inset-0 bg-gray-100 flex items-center justify-center">
      <div class="text-gray-500">加载图片中...</div>
    </div>
    
    <!-- 控制面板 -->
    <div class="controls mt-4 flex flex-wrap gap-3">
      <!-- 模式切换 -->
      <div class="flex items-center gap-2">
        <button
          @click="toggleMode"
          :class="[
            'flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all',
            mode === 'draw' 
              ? 'bg-primary-400 text-white hover:bg-primary-500 shadow-primary-400/30' 
              : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
          ]"
        >
          <svg v-if="mode === 'draw'" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
            <path stroke-linecap="round" stroke-linejoin="round" d="m13.19 8.688-3.72-3.72a4.5 4.5 0 0 0-6.364 6.364l10.94 10.94a2.25 2.25 0 0 0 3.182 0l6.172-6.172a4.5 4.5 0 0 0-6.364-6.364L13.19 8.688Zm0 0L3.93 18.06a2.25 2.25 0 0 1-2.25-2.25l10.94-10.94m0 0a2.25 2.25 0 0 1 2.25 2.25l-6.172 6.172m-1.5-1.5L16.5 5.25" />
          </svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
            <path stroke-linecap="round" stroke-linejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
          </svg>
          {{ mode === 'draw' ? '画笔模式' : '橡皮模式' }}
        </button>
      </div>
      
      <!-- 画笔粗细 -->
      <div class="flex items-center gap-2">
        <label class="text-sm font-medium text-gray-600">画笔粗细</label>
        <input
          type="range"
          min="1"
          max="50"
          step="1"
          v-model="localBrushSize"
          class="w-40 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-400"
        />
        <span class="text-sm text-gray-600">{{ localBrushSize }}px</span>
      </div>
      
      <!-- 清除按钮 -->
      <button
        @click="clearCanvas"
        class="px-4 py-2 bg-red-100 text-red-600 rounded-lg font-medium hover:bg-red-200 transition-all"
      >
        清除画布
      </button>
      
      <!-- 保存按钮 -->
      <button
        @click="saveMask"
        class="px-4 py-2 bg-green-100 text-green-600 rounded-lg font-medium hover:bg-green-200 transition-all"
      >
        保存掩码
      </button>
    </div>
  </div>
</template>

<style scoped>
.brush-canvas-container {
  display: flex;
  flex-direction: column;
  align-items: center;
}

canvas {
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  max-width: 100%;
  max-height: 600px;
  object-fit: contain;
}

.controls {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 1rem;
}
</style>
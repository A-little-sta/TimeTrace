<template>
  <div class="time-engine-wrapper h-full flex bg-gradient-to-br from-[#0a0806] via-[#1a1611] to-[#0c0a08] text-white font-sans relative overflow-hidden">
    
    <!-- 背景流光效果 -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-[#d4af37] to-transparent animate-pulse"></div>
      <div class="absolute top-1/4 left-0 w-1/2 h-px bg-gradient-to-r from-[#d4af37]/20 to-transparent"></div>
      <div class="absolute bottom-1/3 right-0 w-1/3 h-px bg-gradient-to-l from-[#d4af37]/20 to-transparent"></div>
      <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_rgba(212,175,55,0.03)_0%,_transparent_70%)]"></div>
    </div>
    
    <input type="file" ref="fileInput" class="hidden" accept="image/jpeg, image/png, image/webp" @change="handleFileChange"/>

    <transition name="fade">
      <div v-if="!originalImage" class="absolute inset-0 z-10 flex flex-col items-center justify-center">
        <!-- 流光背景 -->
        <div class="absolute inset-0 bg-gradient-to-br from-[#0a0806] via-[#1a1611] to-[#0c0a08] pointer-events-none"></div>
        <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_rgba(212,175,55,0.1)_0%,_transparent_70%)] pointer-events-none"></div>
        
        <!-- 时光之门 -->
        <div class="relative w-[600px] h-[600px] flex items-center justify-center group cursor-pointer" @click="triggerUpload" @dragover.prevent="isDragging = true" @dragleave.prevent="isDragging = false" @drop.prevent="handleDrop">
          
          <!-- 外层光环 -->
          <div class="absolute inset-0 border-2 border-[#d4af37]/20 rounded-full border-dashed animate-[spin_40s_linear_infinite_reverse] glow-ring"></div>
          <div class="absolute inset-8 border border-[#d4af37]/30 rounded-full shadow-[0_0_60px_rgba(212,175,55,0.3)] animate-[spin_60s_linear_infinite] glow-ring"></div>
          
          <!-- 核心能量场 -->
          <div class="absolute inset-20 bg-gradient-to-br from-[#1a1611] via-[#2a2216] to-[#1a1611] border border-[#d4af37]/50 rounded-full shadow-[0_0_100px_rgba(212,175,55,0.4)] flex flex-col items-center justify-center transition-all duration-500 group-hover:scale-110 group-hover:shadow-[0_0_150px_rgba(212,175,55,0.6)] group-hover:border-[#d4af37]/80 core-energy-field z-20">
            
            <!-- 能量核心 -->
                    <div class="relative mb-6">
                      <div class="w-24 h-24 bg-gradient-to-br from-[#d4af37] to-[#f9e0a2] rounded-full shadow-[0_0_50px_rgba(212,175,55,0.8)] animate-pulse"></div>
                      <FontAwesomeIcon :icon="faMagicWandSparkles" class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-4xl text-[#0a0806] drop-shadow-[0_0_10px_rgba(212,175,55,0.8)]" />
                    </div>
            
            <h1 class="text-6xl font-black tracking-[0.3em] bg-clip-text text-transparent bg-gradient-to-r from-[#f9e0a2] via-[#d4af37] to-[#b8860b] drop-shadow-[0_0_30px_rgba(212,175,55,0.8)] mb-4">时光引擎</h1>
            <p class="text-[#d4af37] text-sm tracking-[0.4em] uppercase font-bold drop-shadow-[0_0_20px_rgba(212,175,55,0.5)]">基于 Flux 节点流重塑</p>
            
            <div class="mt-10 px-8 py-3 rounded-full border-2 border-[#d4af37]/50 text-[#f9e0a2] text-base tracking-widest font-bold bg-gradient-to-r from-[#d4af37]/10 to-[#b8860b]/10 transition-all duration-300 group-hover:bg-gradient-to-r group-hover:from-[#d4af37]/20 group-hover:to-[#b8860b]/20 group-hover:scale-105 group-hover:shadow-[0_0_30px_rgba(212,175,55,0.4)]">
              点击或拖曳注入影像
            </div>
          </div>
        </div>

        <!-- 拖拽提示 -->
        <div v-if="isDragging" class="absolute inset-0 z-50 bg-[#0a0806]/95 backdrop-blur-xl flex items-center justify-center border-4 border-[#d4af37] border-dashed">
          <div class="text-[#f9e0a2] text-3xl font-bold tracking-[0.3em] animate-pulse flex flex-col items-center">
            <div class="w-20 h-20 bg-gradient-to-br from-[#d4af37] to-[#f9e0a2] rounded-full flex items-center justify-center mb-6 shadow-[0_0_40px_rgba(212,175,55,0.8)]">
              <el-icon class="text-4xl text-[#0a0806]"><UploadFilled /></el-icon>
            </div>
            释放以对接引擎
          </div>
        </div>
      </div>
    </transition>

    <transition name="fade">
      <div v-if="originalImage" class="absolute inset-0 z-20 flex p-8 gap-8">
        
        <!-- 左侧控制面板 -->
        <aside class="control-panel w-[380px] flex flex-col shrink-0 animate-[slide-in-left_0.6s_ease-out]">
          <header class="mb-8 pl-4">
            <h2 class="text-4xl font-black tracking-[0.2em] bg-clip-text text-transparent bg-gradient-to-r from-[#f9e0a2] to-[#d4af37] drop-shadow-[0_0_20px_rgba(212,175,55,0.5)]">时光引擎</h2>
            <p class="text-[#d4af37]/80 text-sm mt-3 tracking-[0.2em] uppercase font-semibold">Flux.1 Core Pipeline</p>
          </header>

          <div class="panel-card flex-1 bg-gradient-to-b from-[#1a1611]/90 to-[#0c0a08]/90 backdrop-blur-2xl border border-[#d4af37]/30 rounded-3xl shadow-[0_0_60px_rgba(212,175,55,0.2)] p-8 flex flex-col relative overflow-hidden">
            
            <!-- 面板顶部流光 -->
            <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-[#d4af37] to-transparent shadow-[0_0_20px_rgba(212,175,55,0.6)]"></div>

            <!-- 图片预览 -->
            <div class="mb-8 relative group bg-gradient-to-br from-[#2a2216] to-[#1a1611] p-3 shadow-[0_0_40px_rgba(212,175,55,0.3)] border border-[#d4af37]/40 rotate-[-1deg] transition-all duration-500 hover:rotate-0 hover:scale-105 cursor-pointer" @click="triggerUpload">
              <img :src="originalImage" class="w-full aspect-square object-cover opacity-95" />
              <div class="absolute inset-0 bg-gradient-to-t from-[#0a0806]/80 to-transparent flex items-end justify-center pb-3 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                <span class="text-[#f9e0a2] text-xs tracking-widest font-semibold">点击重新载入</span>
              </div>
            </div>

            <!-- 执行流程 -->
            <div class="flex-1">
              <h4 class="text-[#d4af37]/60 text-xs uppercase tracking-[0.3em] border-b border-[#d4af37]/20 pb-3 mb-8 font-bold">EXECUTION FLOW</h4>
              
              <div class="border-l-2 border-gradient-to-b from-[#d4af37] to-[#b8860b] pl-6 py-2 space-y-10 relative ml-3">
                <div class="relative">
                  <div class="absolute -left-[30px] top-1 w-4 h-4 bg-gradient-to-br from-[#d4af37] to-[#f9e0a2] rounded-full shadow-[0_0_15px_rgba(212,175,55,0.8)] animate-pulse"></div>
                  <p class="text-[#f9e0a2] text-base font-bold mb-2 drop-shadow-[0_0_10px_rgba(212,175,55,0.5)]">影像解析</p>
                  <p class="text-[#d4af37]/70 text-xs">噪点特征提取 / 结构重组</p>
                </div>
                <div class="relative">
                  <div class="absolute -left-[30px] top-1 w-4 h-4 bg-gradient-to-br from-[#d4af37] to-[#f9e0a2] rounded-full shadow-[0_0_15px_rgba(212,175,55,0.8)]"></div>
                  <p class="text-[#f9e0a2] text-base font-bold mb-2 drop-shadow-[0_0_10px_rgba(212,175,55,0.5)]">Flux 核心引擎</p>
                  <p class="text-[#d4af37]/70 text-xs">潜空间重绘 (Strength: 0.85)</p>
                </div>
                <div class="relative">
                  <div class="absolute -left-[30px] top-1 w-4 h-4 bg-gradient-to-br from-[#d4af37] to-[#f9e0a2] rounded-full shadow-[0_0_15px_rgba(212,175,55,0.8)]"></div>
                  <p class="text-[#f9e0a2] text-base font-bold mb-2 drop-shadow-[0_0_10px_rgba(212,175,55,0.5)]">面部/细节强化</p>
                  <p class="text-[#d4af37]/70 text-xs">Adetailer 局部修复技术</p>
                </div>
              </div>
            </div>

            <!-- 启动按钮 -->
            <button 
              @click="handleStart"
              :disabled="isProcessing"
              class="mt-8 w-full py-5 rounded-2xl font-black text-[#0a0806] transition-all duration-500 shadow-[0_0_40px_rgba(212,175,55,0.4)] flex items-center justify-center gap-3 relative overflow-hidden group"
              :class="isProcessing ? 'bg-gray-600 cursor-not-allowed' : 'bg-gradient-to-r from-[#f9e0a2] via-[#d4af37] to-[#b8860b] hover:shadow-[0_0_60px_rgba(212,175,55,0.6)] hover:scale-105 cursor-pointer'"
            >
              <span class="relative z-10 flex items-center gap-3 text-lg tracking-widest drop-shadow-[0_0_10px_rgba(212,175,55,0.8)]">
                <el-icon v-if="isProcessing" class="animate-spin text-2xl"><Loading /></el-icon>
                <el-icon v-else class="text-2xl"><VideoPlay /></el-icon>
                {{ isProcessing ? `运算中 ${progress}%` : '启动时空重塑' }}
              </span>
              <div v-if="!isProcessing" class="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700"></div>
            </button>
          </div>
        </aside>

        <!-- 右侧工作区 -->
        <main class="workspace flex-1 bg-gradient-to-br from-[#1a1611]/50 to-[#0c0a08]/50 backdrop-blur-2xl border border-[#d4af37]/20 rounded-3xl shadow-[inset_0_0_100px_rgba(212,175,55,0.1)] relative overflow-hidden flex items-center justify-center">
          
          <div class="preview-container w-full h-full p-8 flex items-center justify-center relative">
            
            <div class="image-wrapper relative shadow-[0_0_120px_rgba(212,175,55,0.3)] rounded-2xl overflow-hidden select-none max-w-full max-h-full flex items-center justify-center bg-gradient-to-br from-[#0a0806] to-[#1a1611]">
              
              <img 
                :src="restoredImages.length > 0 ? restoredImages[activeIndex] : originalImage" 
                class="block max-w-full max-h-[80vh] object-contain transition-all duration-1000" 
                :class="{'grayscale opacity-30 blur-lg': isProcessing}"
                alt="Base"
              />

              <!-- 多图缩略图切换器 -->
              <div v-if="restoredImages.length > 1 && !isProcessing" class="absolute bottom-4 z-40 flex items-center justify-center gap-3 bg-black/30 backdrop-blur-md px-4 py-2 rounded-full border border-[#d4af37]/30 shadow-[0_0_20px_rgba(212,175,55,0.3)]">
                <div 
                  v-for="(imgUrl, index) in restoredImages" 
                  :key="index"
                  @click="activeIndex = index"
                  class="relative w-10 h-10 rounded-md overflow-hidden cursor-pointer transition-all duration-300 transform hover:scale-110"
                  :class="activeIndex === index ? 'border-2 border-[#d4af37] shadow-[0_0_15px_rgba(212,175,55,0.8)] scale-110' : 'border border-white/40 opacity-60 hover:opacity-100'"
                >
                  <img :src="imgUrl" class="w-full h-full object-cover" />
                  
                  <div v-if="activeIndex === index" class="absolute inset-0 bg-gradient-to-t from-[#d4af37]/40 to-transparent"></div>
                </div>
              </div>

              <!-- 处理中效果 -->
              <div v-if="isProcessing" class="absolute inset-0 z-20 overflow-hidden rounded-2xl pointer-events-none">
                <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-[#d4af37] to-transparent shadow-[0_0_30px_10px_rgba(212,175,55,0.8)] scanner-line"></div>
                <div class="absolute inset-0 flex items-center justify-center flex-col bg-[#0a0806]/80 backdrop-blur-sm">
                  <div class="w-20 h-20 bg-gradient-to-br from-[#d4af37] to-[#f9e0a2] rounded-full flex items-center justify-center mb-6 shadow-[0_0_40px_rgba(212,175,55,0.8)] animate-pulse">
                    <el-icon class="text-3xl text-[#0a0806]"><Loading /></el-icon>
                  </div>
                  <span class="text-[#f9e0a2] tracking-[0.4em] text-lg font-black drop-shadow-[0_0_20px_rgba(212,175,55,0.8)]">FLUX 节点深度解析中</span>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { faMagicWandSparkles, faSpinner, faPlay, faUpload } from '@fortawesome/free-solid-svg-icons'

const fileInput = ref<HTMLInputElement | null>(null)
const isDragging = ref(false)
const originalImage = ref<string | null>(null)
const restoredImages = ref<string[]>([]) // 改为数组，支持多图
const activeIndex = ref(0) // 当前显示的图片索引
const isProcessing = ref(false)
const progress = ref(0)
const currentFile = ref<File | null>(null)

const triggerUpload = () => fileInput.value?.click()

const handleFileChange = (e: Event) => {
  const target = e.target as HTMLInputElement
  if (target.files && target.files[0]) loadFile(target.files[0])
}

const handleDrop = (e: DragEvent) => {
  isDragging.value = false
  if (e.dataTransfer?.files && e.dataTransfer.files[0]) loadFile(e.dataTransfer.files[0])
}

const loadFile = (file: File) => {
  currentFile.value = file
  originalImage.value = URL.createObjectURL(file)
  restoredImages.value = []
  activeIndex.value = 0
}

const handleStart = async () => {
  if (!originalImage.value || !currentFile.value) return
  isProcessing.value = true
  progress.value = 0
  
  try {
    // 1. 准备 FormData
    const formData = new FormData()
    formData.append('file', currentFile.value)

    // 2. 调用启动接口
    const startRes = await fetch('http://localhost:8000/api/time-engine/repair', {
      method: 'POST',
      body: formData
    })

    if (!startRes.ok) {
      throw new Error(`启动失败: ${startRes.status}`)
    }

    const startData = await startRes.json()
    const promptId = startData.prompt_id
    
    // 3. 开始轮询进度 (每 2 秒查一次)
    const pollInterval = setInterval(async () => {
      try {
        // 【关键修复】使用正确的 workshop 任务状态查询接口
        const statusRes = await fetch(`http://localhost:8000/api/v1/workshop/tasks`)
        
        if (!statusRes.ok) {
          throw new Error(`查询失败: ${statusRes.status}`)
        }

        const tasksData = await statusRes.json()
        // 找到当前用户的最新时光引擎任务
        const currentTask = tasksData.find(task => 
          task.task_type === 'time_engine' && 
          (task.status === 'processing' || task.status === 'completed')
        )
        
        if (!currentTask) {
          throw new Error("未找到时光引擎任务")
        }
        
        const statusData = currentTask
        
        if (statusData.status === 'processing') {
          // 此时可以让进度条缓慢增加，保持动效，不要直接跳到100
          if (progress.value < 90) progress.value += 5
        } else if (statusData.status === 'completed') {
          // 4. 任务完成！接收所有图片数组
          clearInterval(pollInterval)
          progress.value = 100
          
          // 【修复】更智能的 URL 拼接逻辑
          const getFullUrl = (path: string) => {
            if (!path) return '';
            // 如果已经是完整 URL (http开头)，直接返回
            if (path.startsWith('http://') || path.startsWith('https://')) {
              return path;
            }
            // 如果是绝对路径 (/static 开头)，只拼域名
            if (path.startsWith('/')) {
              return `http://localhost:8000${path}`;
            }
            // 其他情况 (相对路径)，拼域名+static
            return `http://localhost:8000/static/${path}`;
          };
          
          if (statusData.step_results && statusData.step_results.length > 0) {
            restoredImages.value = statusData.step_results.map(getFullUrl)
          } else if (statusData.result_urls && statusData.result_urls.length > 0) {
            restoredImages.value = statusData.result_urls
          } else if (statusData.result_path) {
            restoredImages.value = [getFullUrl(statusData.result_path)]
          } else {
            restoredImages.value = []
          }
          
          activeIndex.value = 0 // 默认显示第一张
          isProcessing.value = false
        } else if (statusData.status === 'failed') {
          clearInterval(pollInterval)
          isProcessing.value = false
          alert(`时光引擎运行失败: ${statusData.message}`)
        }
      } catch (err) {
        console.error("查询进度失败", err)
        clearInterval(pollInterval)
        isProcessing.value = false
        alert("查询进度失败，请检查后端连接")
      }
    }, 2000)

  } catch (error) {
    console.error("时光引擎启动失败", error)
    isProcessing.value = false
    alert("引擎过热，启动失败，请检查后端连接")
  }
}
</script>

<style scoped>
/* 高级白金琉璃特效 */

/* 流光光环 */
.glow-ring {
  filter: drop-shadow(0 0 8px rgba(212, 175, 55, 0.3));
}

/* 核心能量场 */
.core-energy-field {
  backdrop-filter: blur(16px);
  background: linear-gradient(145deg, 
    rgba(26, 22, 17, 0.95) 0%, 
    rgba(42, 34, 22, 0.9) 50%, 
    rgba(26, 22, 17, 0.95) 100%);
}

/* 控制面板动画 */
@keyframes slide-in-left {
  0% {
    opacity: 0;
    transform: translateX(-30px);
  }
  100% {
    opacity: 1;
    transform: translateX(0);
  }
}

/* 扫描线动画 */
.scanner-line {
  animation: scan 2.5s cubic-bezier(0.4, 0, 0.2, 1) infinite alternate;
}
@keyframes scan {
  0% { top: 0%; opacity: 0; }
  10% { opacity: 1; }
  90% { opacity: 1; }
  100% { top: 100%; opacity: 0; }
}

/* 过渡动画 */
.fade-enter-active, .fade-leave-active { 
  transition: all 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94); 
}
.fade-enter-from, .fade-leave-to { 
  opacity: 0; 
  transform: scale(0.95);
}

/* 响应式优化 */
@media (max-width: 1024px) {
  .control-panel {
    width: 320px;
  }
  
  .workspace {
    padding: 1.5rem;
  }
}

@media (max-width: 768px) {
  .time-engine-wrapper {
    flex-direction: column;
  }
  
  .control-panel {
    width: 100%;
    margin-bottom: 1rem;
  }
  
  .workspace {
    height: 60vh;
  }
}

/* 图片预览悬停效果 */
.preview-container .image-wrapper:hover {
  transform: scale(1.02);
  box-shadow: 0 0 150px rgba(212, 175, 55, 0.5);
}

/* 按钮悬停效果 */
button:not(:disabled):hover {
  transform: translateY(-2px);
  filter: brightness(1.1);
}

/* 文字发光效果 */
.drop-shadow-gold {
  filter: drop-shadow(0 0 10px rgba(212, 175, 55, 0.5));
}

/* 面板卡片效果 */
.panel-card {
  position: relative;
  overflow: hidden;
}

.panel-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
  transition: left 0.5s ease;
}

.panel-card:hover::before {
  left: 100%;
}
</style>
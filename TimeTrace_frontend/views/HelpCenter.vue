<template>
  <div class="min-h-screen bg-[#F0F2F5] flex justify-center py-6 md:py-12 px-4 md:px-6 font-sans text-slate-800">
    <div class="max-w-6xl w-full bg-white/90 backdrop-blur-xl rounded-[2rem] shadow-2xl shadow-slate-200/50 overflow-hidden flex flex-col md:flex-row min-h-[800px] border border-white/50">
      
      <aside class="w-full md:w-80 bg-slate-50/80 border-b md:border-b-0 md:border-r border-gray-100 p-6 flex flex-col shrink-0 z-20">
        <div class="mb-6 md:mb-10 flex flex-row md:flex-col justify-between items-center md:items-start">
          <div>
            <h1 class="font-serif text-2xl md:text-3xl font-bold text-slate-900">功能指南</h1>
            <p class="hidden md:block text-xs text-slate-500 mt-2">选择最适合的 AI 魔法</p>
          </div>
          <div class="md:hidden text-primary">
            <FontAwesomeIcon icon="fa-solid fa-wand-magic-sparkles" class="text-xl" />
          </div>
        </div>
 
        <nav class="flex md:flex-col gap-3 overflow-x-auto md:overflow-visible pb-2 md:pb-0 scrollbar-hide -mx-6 px-6 md:mx-0 md:px-0">
          <button v-for="tab in tabs" :key="tab.id"
            @click="currentTab = tab.id"
            class="flex-shrink-0 w-auto md:w-full text-left px-4 py-3 md:px-5 md:py-4 rounded-xl transition-all duration-300 flex items-center gap-3 border whitespace-nowrap"
            :class="currentTab === tab.id 
              ? 'bg-white shadow-lg shadow-slate-200 text-slate-900 border-slate-100 scale-[1.02]' 
              : 'bg-transparent text-slate-500 border-transparent hover:bg-slate-100 hover:text-slate-700'">
            
            <div class="w-8 h-8 rounded-lg flex items-center justify-center transition-colors shadow-sm"
              :class="currentTab === tab.id ? 'bg-gray-900 text-white' : 'bg-slate-200 text-slate-400'">
              <FontAwesomeIcon :icon="[tab.icon.split(' ')[0], tab.icon.split(' ')[1]]" />
            </div>
            <span class="font-bold text-sm md:text-base">{{ tab.title }}</span>
          </button>
        </nav>
        
        <div class="hidden md:block mt-auto bg-gradient-to-br from-indigo-50 to-purple-50 rounded-2xl p-5 border border-indigo-100/50">
          <div class="flex items-center gap-2 mb-2">
            <div class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
            <h4 class="text-indigo-900 font-bold text-sm">遇到问题？</h4>
          </div>
          <p class="text-xs text-indigo-700/70 mb-3 leading-relaxed">如果不确定该用哪个功能，可以上传照片让 AI 自动推荐。</p>
          <button class="text-xs font-bold text-indigo-600 hover:text-indigo-800 transition-colors flex items-center">
            联系客服支持 <FontAwesomeIcon icon="fa-solid fa-headset" class="ml-1.5" />
          </button>
        </div>
      </aside>
 
      <main class="flex-1 overflow-y-auto relative bg-white custom-scrollbar">
        <transition name="fade-slide" mode="out-in">
          <div :key="currentTab" class="p-6 md:p-16 max-w-3xl mx-auto">
            
            <div class="mb-10 text-center md:text-left">
              <span class="inline-block px-3 py-1 rounded-full bg-slate-100 text-slate-500 font-bold tracking-widest text-[10px] uppercase mb-4">
                Feature Guide
              </span>
              <h2 class="font-serif text-3xl md:text-5xl font-bold text-slate-900 mb-4 tracking-tight">
                {{ activeData.title }}
              </h2>
              <p class="text-lg md:text-xl text-slate-500 font-light leading-relaxed">
                {{ activeData.subtitle }}
              </p>
              
              <!-- 时光引擎特色标识 -->
              <div v-if="currentTab === 'time_engine'" class="mt-6 bg-gradient-to-r from-yellow-50 to-amber-50 border-l-4 border-yellow-400 p-4 rounded-lg">
                <div class="flex items-center">
                  <div class="w-3 h-3 rounded-full bg-yellow-400 animate-pulse mr-3"></div>
                  <span class="text-yellow-700 font-bold text-sm">✨ 核心特色模块 · AI重绘您的照片</span>
                </div>
              </div>
            </div>
 
            <div class="mb-14">
              <div class="flex justify-between items-end mb-4">
                <h3 class="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                  <span class="w-1.5 h-1.5 rounded-full bg-black"></span> 
                  {{ currentTab === 'voice' ? '音频预览' : currentTab === 'liveportrait' ? '视频预览' : '效果预览' }}
                </h3>
                <span v-if="currentTab !== 'voice' && currentTab !== 'liveportrait'" class="text-xs text-slate-400 bg-slate-50 px-2 py-1 rounded border border-slate-100">
                  <FontAwesomeIcon icon="fa-solid fa-arrows-left-right" class="mr-1" /> 拖拽中间滑块对比
                </span>
              </div>

              <!-- 音频功能预览 -->
              <div v-if="currentTab === 'voice'" class="bg-gradient-to-br from-blue-50 to-purple-50 rounded-2xl p-8 border border-blue-100/50">
                <div class="flex flex-col items-center justify-center text-center">
                  <div class="w-20 h-20 mb-6 text-blue-500 bg-white rounded-full flex items-center justify-center shadow-lg">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M19.114 5.636a9 9 0 010 12.728M16.463 8.288a5.25 5.25 0 010 7.424M6.75 8.25l4.72-4.72a.75.75 0 011.28.53v15.88a.75.75 0 01-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.01 9.01 0 012.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75z" />
                    </svg>
                  </div>
                  
                  <h3 class="text-xl font-bold text-slate-900 mb-3">留音语音功能</h3>
                  <p class="text-slate-600 mb-6 leading-relaxed">支持文本转语音和声音复活两种模式，让您的照片开口说话</p>
                  
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-2xl">
                    <div class="bg-white/80 rounded-xl p-4 border border-blue-100/50">
                      <div class="flex items-center mb-3">
                        <div class="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 mr-3">
                          <FontAwesomeIcon icon="fa-solid fa-keyboard" />
                        </div>
                        <h4 class="font-bold text-slate-900">文本转语音</h4>
                      </div>
                      <p class="text-sm text-slate-600">输入文字，选择音色，即可生成自然流畅的语音</p>
                    </div>
                    
                    <div class="bg-white/80 rounded-xl p-4 border border-purple-100/50">
                      <div class="flex items-center mb-3">
                        <div class="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center text-purple-600 mr-3">
                          <FontAwesomeIcon icon="fa-solid fa-microphone" />
                        </div>
                        <h4 class="font-bold text-slate-900">声音复活</h4>
                      </div>
                      <p class="text-sm text-slate-600">上传参考音频，克隆相似声音，让照片中的声音重现</p>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- 灵动功能预览 -->
              <div v-else-if="currentTab === 'liveportrait'" class="bg-gradient-to-br from-green-50 to-teal-50 rounded-2xl p-8 border border-green-100/50">
                <div class="flex flex-col items-center justify-center text-center">
                  <div class="w-20 h-20 mb-6 text-green-500 bg-white rounded-full flex items-center justify-center shadow-lg">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25h-9A2.25 2.25 0 002.25 7.5v9a2.25 2.25 0 002.25 2.25z" />
                    </svg>
                  </div>
                  
                  <h3 class="text-xl font-bold text-slate-900 mb-3">灵动人像功能</h3>
                  <p class="text-slate-600 mb-6 leading-relaxed">让静态照片动起来，赋予人像生动的表情和动作，重现当年的音容笑貌</p>
                  
                  <div class="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-3xl">
                    <div class="bg-white/80 rounded-xl p-4 border border-green-100/50">
                      <div class="flex items-center mb-3">
                        <div class="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center text-green-600 mr-3">
                          <FontAwesomeIcon icon="fa-solid fa-face-smile" />
                        </div>
                        <h4 class="font-bold text-slate-900">表情生动</h4>
                      </div>
                      <p class="text-sm text-slate-600">AI智能生成自然的微笑、眨眼等面部表情变化</p>
                    </div>
                    
                    <div class="bg-white/80 rounded-xl p-4 border border-teal-100/50">
                      <div class="flex items-center mb-3">
                        <div class="w-8 h-8 rounded-full bg-teal-100 flex items-center justify-center text-teal-600 mr-3">
                          <FontAwesomeIcon icon="fa-solid fa-user" />
                        </div>
                        <h4 class="font-bold text-slate-900">头部动作</h4>
                      </div>
                      <p class="text-sm text-slate-600">生成自然的头部转动、点头等动作，让照片活起来</p>
                    </div>
                    
                    <div class="bg-white/80 rounded-xl p-4 border border-emerald-100/50">
                      <div class="flex items-center mb-3">
                        <div class="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-600 mr-3">
                          <FontAwesomeIcon icon="fa-solid fa-microphone-lines" />
                        </div>
                        <h4 class="font-bold text-slate-900">口型同步</h4>
                      </div>
                      <p class="text-sm text-slate-600">支持音频驱动，让照片中的人物开口说话，口型自然同步</p>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- 图片功能预览 -->
              <div v-else>
                <CompareSlider 
                  :beforeImage="activeData.beforeImage" 
                  :afterImage="activeData.afterImage"
                  :title="activeData.shortTitle"
                  :description="activeData.subtitle"
                  :autoAnimate="true"
                  className="w-full aspect-video"
                />
                <p class="mt-3 text-center text-sm text-slate-500 italic">{{ activeData.demoDesc }}</p>
              </div>
            </div>
 
            <div class="mb-12">
              <h3 class="text-xs font-bold text-slate-900 uppercase tracking-wider mb-5 flex items-center gap-2">
                 <span class="w-1.5 h-1.5 rounded-full bg-green-500"></span> 适用场景
              </h3>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div v-for="(scene, idx) in activeData.scenes" :key="idx" 
                  class="bg-slate-50 hover:bg-slate-100 p-4 rounded-xl border border-slate-100 transition-colors flex items-start gap-3 group">
                  <div class="w-8 h-8 rounded-full bg-white border border-slate-100 flex items-center justify-center text-slate-400 group-hover:text-indigo-500 transition-colors shrink-0">
                    <FontAwesomeIcon icon="fa-solid fa-check" class="text-xs" />
                  </div>
                  <span class="text-slate-700 text-sm leading-relaxed mt-1">{{ scene }}</span>
                </div>
              </div>
            </div>

            <!-- 时光引擎技术特点 -->
            <div v-if="currentTab === 'time_engine'" class="mb-12">
              <h3 class="text-xs font-bold text-slate-900 uppercase tracking-wider mb-5 flex items-center gap-2">
                 <span class="w-1.5 h-1.5 rounded-full bg-blue-500"></span> 技术特点
              </h3>
              <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div class="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-6 border border-blue-100/50">
                  <div class="flex items-center mb-3">
                    <div class="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 mr-3">
                      <FontAwesomeIcon icon="fa-solid fa-diagram-project" />
                    </div>
                    <h4 class="font-bold text-slate-900">节点流工作流</h4>
                  </div>
                  <p class="text-sm text-slate-600">基于ComfyUI的可视化节点编辑，支持并行处理和灵活配置</p>
                </div>
                
                <div class="bg-gradient-to-br from-purple-50 to-pink-50 rounded-2xl p-6 border border-purple-100/50">
                  <div class="flex items-center mb-3">
                    <div class="w-10 h-10 rounded-full bg-purple-100 flex items-center justify-center text-purple-600 mr-3">
                      <FontAwesomeIcon icon="fa-solid fa-brain" />
                    </div>
                    <h4 class="font-bold text-slate-900">Flux模型引擎</h4>
                  </div>
                  <p class="text-sm text-slate-600">采用Flux模型，支持8K超高清图像修复</p>
                </div>
                
                <div class="bg-gradient-to-br from-amber-50 to-orange-50 rounded-2xl p-6 border border-amber-100/50">
                  <div class="flex items-center mb-3">
                    <div class="w-10 h-10 rounded-full bg-amber-100 flex items-center justify-center text-amber-600 mr-3">
                      <FontAwesomeIcon icon="fa-solid fa-wand-magic-sparkles" />
                    </div>
                    <h4 class="font-bold text-slate-900">智能理解修复</h4>
                  </div>
                  <p class="text-sm text-slate-600">AI深度理解图像内容，进行创造性修复而非简单填补</p>
                </div>
              </div>
            </div>
 
            <div class="bg-amber-50/50 border border-amber-100/80 rounded-2xl p-6 relative overflow-hidden">
               <FontAwesomeIcon icon="fa-solid fa-triangle-exclamation" class="absolute -right-4 -bottom-4 text-8xl text-amber-100/50 -rotate-12" />
               
               <div class="relative z-10">
                 <h3 class="text-xs font-bold text-amber-800 uppercase mb-2 flex items-center gap-2">
                    <FontAwesomeIcon icon="fa-solid fa-circle-info" /> 局限性与建议
                 </h3>
                 <p class="text-sm text-amber-900/70 leading-relaxed">
                   {{ activeData.limitations }}
                 </p>
               </div>
            </div>
 
            <div class="mt-12 pt-8 border-t border-gray-100 text-center">
              <router-link :to="getWorkshopLink(currentTab)" 
                class="group inline-flex items-center justify-center px-8 py-4 bg-slate-900 text-white rounded-full font-bold shadow-xl shadow-slate-900/20 hover:bg-black hover:scale-105 hover:shadow-2xl transition-all duration-300">
                <span>立即尝试 · {{ activeData.shortTitle }}</span>
                <FontAwesomeIcon icon="fa-solid fa-arrow-right" class="ml-2 group-hover:translate-x-1 transition-transform" />
              </router-link>
            </div>
 
          </div>
        </transition>
      </main>
 
    </div>
  </div>
</template>
 
<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
import CompareSlider from '../components/CompareSlider.vue';

// 定义接口，增强代码健壮性
interface FeatureData {
  title: string;
  shortTitle: string; // 用于按钮
  subtitle: string;
  scenes: string[];
  beforeImage: string; // 修复前
  afterImage: string;  // 修复后
  demoDesc: string;
  limitations: string;
}

const currentTab = ref<string>('dustless');
const sliderPosition = ref(50); // 对比滑块位置 (0-100)
const isSliding = ref(false);

// 切换Tab时重置滑块
watch(currentTab, () => {
  sliderPosition.value = 50;
});

const tabs = [
  { id: 'time_engine', title: '时光引擎 (核心)', icon: 'fa-solid fa-hourglass-half' },
  { id: 'dustless', title: '拂尘 (去瑕疵)', icon: 'fa-solid fa-wand-magic-sparkles' },
  { id: 'dustless_denoise', title: '拂尘 (去噪)', icon: 'fa-solid fa-wand-magic-sparkles' },
  { id: 'liuguang', title: '流光 (上色)', icon: 'fa-solid fa-palette' },
  { id: 'qingying', title: '清影 (超清)', icon: 'fa-solid fa-mountain-sun' },
  { id: 'zhenrong', title: '真容 (人脸)', icon: 'fa-regular fa-face-smile' },
  { id: 'voice', title: '留音 (语音)', icon: 'fa-solid fa-microphone' },
  { id: 'liveportrait', title: '灵动 (人像)', icon: 'fa-solid fa-video' }
];

// 使用 Record 工具类型
const contentData: Record<string, FeatureData> = {
  time_engine: {
    title: '时光引擎 · 智能重生',
    shortTitle: '时光引擎',
    subtitle: '基于Flux模型的AIGC智能修复，一键式解决严重破损照片，让岁月痕迹消失无踪。',
    scenes: [
      '严重破损、撕裂、霉变的老照片修复',
      '大面积褪色、模糊、失真的照片重生',
      '需要整体重构和细节重绘的珍贵照片',
      '希望获得艺术级修复效果的经典照片'
    ],
    beforeImage: './assets/images/AI前.png', 
    afterImage: './assets/images/AI后.png',
    demoDesc: '拖动滑块查看：AI如何基于节点流工作流，智能理解并重绘严重破损的照片。',
    limitations: '对于极端严重的照片损坏，可能需要较长的处理时间。建议使用高分辨率原始照片以获得最佳效果。时光引擎会基于AI理解进行创造性修复，可能与原始照片存在艺术性差异。'
  },
  dustless: {
    title: '拂尘 · 物理修复',
    shortTitle: '拂尘去瑕',
    subtitle: '像文物修复师一样，智能识别并填补岁月的缺憾，抹去折痕与污渍。',
    scenes: [
      '带有明显折痕、撕裂缝隙的老照片',
      '表面有霉斑、咖啡渍或墨水的照片',
      '扫描后带有大量灰尘噪点的底片',
      '想要去除画面中简单的杂物或水印'
    ],
    beforeImage: './assets/images/拂尘前.png', 
    afterImage: './assets/images/拂尘后.jpg',
    demoDesc: '拖动滑块查看：AI 如何自动识别并无痕填补复杂的纸张裂痕。',
    limitations: '对于面部五官的严重物理缺失（如眼睛处正好有个大洞），拂尘只能根据周围皮肤纹理填补，无法“凭空猜出”长相。建议修复后结合“真容”模块使用。'
  },
  liuguang: {
    title: '流光 · 色彩复苏',
    shortTitle: '流光上色',
    subtitle: '基于深度学习的色彩分析，让记忆不再只有黑白灰，重现那个年代的温度。',
    scenes: [
      '家里的黑白老照片或底片扫描件',
      '年代久远的黑白视频截图',
      '褪色严重的彩色照片（偏红/偏黄矫正）',
      '需要营造艺术氛围的线稿或素描'
    ],
    beforeImage: './assets/images/流光前.jpg', // 黑白
    afterImage: './assets/images/流光后.jpg', // 彩色
    demoDesc: '智能分析衣物材质与环境光，还原最接近历史真实的色彩。',
    limitations: 'AI 对历史特定物体的颜色可能推测不准（如某件制服当年具体的颜色规定）。我们提供了“艺术”与“纪实”两种上色模式供选择。'
  },
  qingying: {
    title: '清影 · 画质重构',
    shortTitle: '清影超清',
    subtitle: '不仅是放大，更是重绘。利用生成式模型，让模糊的瞬间变得锐利清晰。',
    scenes: [
      '由于手抖或对焦失败导致的模糊照片',
      '早年间低像素翻盖手机拍摄的照片',
      '被微信/网络多次转发压缩的马赛克图',
      '需要打印成大幅海报的低清合影'
    ],
    beforeImage: './assets/images/清影前.png', // 模糊低清
    afterImage: './assets/images/清影后.jpg', // 高清
    demoDesc: 'HYPIR 模型重构发丝、衣物纹理等微小细节，分辨率提升 4 倍。',
    limitations: '因为是生成式模型（AIGC），对于极度模糊背景中的小字或远处的人脸，可能会生成出“不存在的细节”（幻觉）。但在风景和静物特写上效果极佳。'
  },
  zhenrong: {
    title: '真容 · 肖像精修',
    shortTitle: '真容精修',
    subtitle: '穿越时空的凝视。专注于面部几何重建，找回亲人最清晰的模样。',
    scenes: [
      '五官模糊不清的大合影（看不清脸）',
      '对焦不准的人像特写',
      '面部有大量噪点或轻微破损的照片'
    ],
    beforeImage: './assets/images/真容前.png', // 模糊人脸
    afterImage: './assets/images/真容后.jpg', // 清晰人脸
    demoDesc: '专注于眼、鼻、嘴的结构重建，显著提升五官立体感与神态清晰度。',
    limitations: '此功能仅针对面部区域生效。如果照片背景也很模糊，强烈建议先使用"清影"修复整体画质，再用"真容"进行面部精修。'
  },
  dustless_denoise: {
    title: '拂尘 · 去噪修复',
    shortTitle: '拂尘去噪',
    subtitle: '基于UHDM超高清降噪算法，智能去除摩尔纹和图像噪声，让照片恢复纯净清晰。',
    scenes: [
      '扫描照片中出现的摩尔纹干扰',
      '数码照片中的噪点和颗粒感',
      '屏幕截图中的图像噪声',
      '老照片的数字噪声和模糊'
    ],
    beforeImage: './assets/images/降噪前.jpg', // 有噪点
    afterImage: './assets/images/降噪后.jpg', // 降噪后
    demoDesc: '拖动滑块查看：AI如何智能识别并去除复杂的摩尔纹和图像噪声。',
    limitations: '对于极端严重的噪声和摩尔纹，可能需要多次处理或结合其他修复功能。建议先使用去噪功能，再进行其他修复。'
  },
  voice: {
    title: '留音 · 语音魔法',
    shortTitle: '留音语音',
    subtitle: '让照片开口说话，赋予静态图像声音的力量。支持文本转语音和声音复活，让记忆更加生动。',
    scenes: [
      '为老照片添加语音描述，讲述照片背后的故事',
      '将文字内容转换为自然流畅的语音播报',
      '基于少量语音样本克隆出相似的声音',
      '为家庭相册制作有声回忆录',
      '为历史照片添加语音解说'
    ],
    beforeImage: './assets/images/voice_preview/male1_preview.wav', // 使用音频预览图
    afterImage: './assets/images/voice_preview/female1_preview.wav', // 使用音频预览图
    demoDesc: '留音模块提供两种模式：文本转语音和声音复活，满足不同的语音生成需求。',
    limitations: '声音复活功能需要提供清晰的参考音频样本，样本质量直接影响克隆效果。文本转语音功能支持多种音色选择，但生成效果受文本内容和长度影响。'
  },
  liveportrait: {
    title: '灵动 · 人像复活',
    shortTitle: '灵动人像',
    subtitle: '让静态照片动起来，赋予人像生动的表情和动作。基于先进的AI技术，让照片中的人物开口说话、展现表情。',
    scenes: [
      '让老照片中的亲人动起来，重现当年的音容笑貌',
      '为历史人物照片添加生动的表情和动作',
      '制作个性化的生日祝福视频',
      '为家庭相册制作动态回忆录',
      '让证件照或肖像照展现自然的微笑表情'
    ],
    beforeImage: './assets/images/liveportrait_preview/before.jpg', // 静态照片
    afterImage: './assets/images/liveportrait_preview/after.mp4', // 动态视频
    demoDesc: '灵动模块通过AI技术分析人像特征，生成自然的头部动作和表情变化，让照片中的人物仿佛活了过来。',
    limitations: '生成效果受原始照片质量影响，清晰度高、光线好的照片效果更佳。处理时间较长，请耐心等待。建议使用正面清晰的人像照片，避免侧脸或模糊图像。'
  }
};

const activeData = computed(() => contentData[currentTab.value]);

// 获取工作坊链接
const getWorkshopLink = (tabId: string) => {
  // 拂尘去噪功能需要特殊处理，导航到拂尘模块并传递参数
  if (tabId === 'dustless_denoise') {
    return `/workshop/dustless?repairType=denoise`;
  }
  return `/workshop/${tabId}`;
};
</script>
 
<style scoped>
/* 自定义过渡动画 */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.4s cubic-bezier(0.2, 0.8, 0.2, 1);
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(10px) scale(0.98);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-10px) scale(0.98);
}

/* 隐藏滚动条但保留功能 */
.scrollbar-hide::-webkit-scrollbar {
    display: none;
}
.scrollbar-hide {
    -ms-overflow-style: none;
    scrollbar-width: none;
}

/* 自定义右侧内容区滚动条 */
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: rgba(203, 213, 225, 0.5);
  border-radius: 20px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background-color: rgba(148, 163, 184, 0.8);
}
</style>
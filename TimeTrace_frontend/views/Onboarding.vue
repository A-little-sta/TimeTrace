<template>
  <div class="min-h-screen bg-[#FCFBF9] font-sans text-slate-800 overflow-x-hidden selection:bg-amber-100 selection:text-amber-900">
    
    <div class="fixed top-1/2 right-6 -translate-y-1/2 z-50 flex flex-col items-center gap-4 hidden md:flex">
      <div 
        v-for="(section, index) in sections" 
        :key="index"
        class="group relative flex items-center justify-end"
      >
        <span class="absolute right-8 px-3 py-1.5 bg-slate-900/90 backdrop-blur text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-all duration-300 translate-x-2 group-hover:translate-x-0 whitespace-nowrap pointer-events-none shadow-xl">
          {{ section.name }}
        </span>
        <button
          @click="scrollTo(index)"
          class="w-2.5 rounded-full transition-all duration-500 ease-out border border-amber-900/10"
          :class="activeSection === index 
            ? 'h-10 bg-amber-600 shadow-[0_0_15px_rgba(217,119,6,0.4)]' 
            : 'h-2.5 bg-amber-900/20 hover:bg-amber-600/50 hover:scale-125'
          "
        ></button>
      </div>
    </div>

    <div class="relative">
      <section ref="heroSection" class="min-h-screen flex items-center justify-center relative overflow-hidden">
        <div class="absolute top-0 right-0 w-[1000px] h-[1000px] bg-gradient-to-bl from-amber-200/40 via-orange-100/20 to-transparent rounded-full blur-[100px] -translate-y-1/3 translate-x-1/4"></div>
        <div class="absolute bottom-0 left-0 w-[800px] h-[800px] bg-gradient-to-tr from-yellow-200/30 via-amber-100/20 to-transparent rounded-full blur-[100px] translate-y-1/3 -translate-x-1/4"></div>
        
        <div class="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGNpcmNsZSBjeD0iMSIgY3k9IjEiIHI9IjEiIGZpbGw9InJnYmEoMTIwLCA5MCwgMjAsIDAuMDUpIi8+PC9zdmc+')] [mask-image:linear-gradient(to_bottom,white,transparent)] pointer-events-none"></div>
        
        <div class="relative z-10 text-center px-6 max-w-5xl mx-auto pt-20">
          <div class="mb-12 transform transition-all duration-1000 translate-y-0 opacity-100">
            <div class="inline-flex items-center gap-2 px-5 py-2.5 bg-white/60 backdrop-blur-md rounded-full text-slate-600 font-medium text-sm border border-amber-900/10 shadow-sm mb-10">
              <span class="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></span>
              AI 多模态影像修复系统
            </div>
            
            <h1 class="font-serif text-7xl md:text-[6.5rem] font-bold text-slate-900 mb-8 leading-tight tracking-tight drop-shadow-sm">
              岁月<span class="text-transparent bg-clip-text bg-gradient-to-r from-amber-600 via-yellow-500 to-amber-500 italic pr-4">笺影</span>
            </h1>
            
            <p class="text-xl md:text-2xl text-slate-500 font-light leading-relaxed max-w-3xl mx-auto">
              基于先进 AI 节点流工作流，让珍贵的老照片重获新生。<br class="hidden md:block"/>重现时光的温度与色彩。
            </p>
          </div>
          
          <div class="flex flex-col sm:flex-row gap-5 justify-center items-center mt-16">
            <button 
              @click="scrollTo(1)"
              class="group px-10 py-4 bg-slate-900 text-white rounded-full font-bold shadow-xl shadow-slate-900/20 hover:bg-slate-800 hover:shadow-2xl hover:-translate-y-1 transition-all duration-300 flex items-center w-full sm:w-auto justify-center text-lg"
            >
              <span>探索七大魔法</span>
              <FontAwesomeIcon icon="fa-solid fa-arrow-down" class="ml-3 group-hover:translate-y-1 transition-transform" />
            </button>
            <button 
              @click="goToApp"
              class="group px-10 py-4 bg-white/80 backdrop-blur-sm text-slate-700 rounded-full font-bold border border-amber-900/10 hover:bg-amber-50 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 w-full sm:w-auto justify-center flex items-center gap-2 text-lg"
            >
              {{ isLoggedIn ? '进入工作台' : '立即登录系统' }}
              <FontAwesomeIcon icon="fa-solid fa-arrow-right" class="text-sm opacity-50 text-amber-600 group-hover:translate-x-1 transition-transform" />
            </button>
          </div>
        </div>
      </section>

      <section 
        v-for="(feature, index) in features" 
        :key="feature.id"
        :ref="el => { if (el) sectionRefs[index] = el }"
        class="min-h-screen flex items-center py-24 relative overflow-hidden"
        :class="index % 2 === 0 ? 'bg-white' : 'bg-[#FDFBF7]'"
      >
        <div class="max-w-[85rem] mx-auto px-6 lg:px-12 w-full relative z-10">
          <div class="grid lg:grid-cols-12 gap-16 lg:gap-20 items-center">
            
            <div 
              class="lg:col-span-5 transition-all duration-1000"
              :class="{
                'lg:order-2': index % 2 === 1,
                'opacity-0 translate-y-12': activeSection !== index + 1,
                'opacity-100 translate-y-0 delay-100': activeSection === index + 1
              }"
            >
              <div class="mb-10">
                <span class="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-widest mb-6 border" :class="feature.badgeClass">
                  <FontAwesomeIcon :icon="feature.icon" />
                  {{ feature.badge }}
                </span>
                <h2 class="font-serif text-5xl md:text-6xl font-bold text-slate-900 mb-6 leading-[1.15] tracking-tight">
                  {{ feature.title }}
                </h2>
                <p class="text-lg md:text-xl text-slate-500 leading-relaxed font-light">
                  {{ feature.subtitle }}
                </p>
              </div>

              <div class="mb-10">
                <h3 class="text-sm font-bold text-slate-400 uppercase tracking-widest mb-5 flex items-center gap-2">
                  <span class="w-1.5 h-1.5 rounded-full bg-amber-300"></span> 适用场景
                </h3>
                <ul class="space-y-4">
                  <li 
                    v-for="(scene, sceneIndex) in feature.scenes.slice(0, 3)" 
                    :key="sceneIndex"
                    class="flex items-start gap-4 text-slate-700"
                  >
                    <div class="mt-1 w-5 h-5 rounded-full bg-amber-50 flex items-center justify-center shrink-0 border border-amber-200">
                      <FontAwesomeIcon icon="fa-solid fa-check" class="text-amber-500 text-[10px]" />
                    </div>
                    <span class="text-base leading-relaxed">{{ scene }}</span>
                  </li>
                </ul>
              </div>

              <div class="bg-[#FFFBF0] border border-amber-200/60 rounded-2xl p-5 flex gap-4 items-start shadow-sm">
                 <div class="w-6 h-6 rounded-full bg-amber-100 flex items-center justify-center shrink-0 mt-0.5">
                   <FontAwesomeIcon icon="fa-solid fa-info" class="text-amber-600 text-xs" />
                 </div>
                 <p class="text-sm text-amber-800/80 leading-relaxed">{{ feature.limitations }}</p>
              </div>
            </div>

            <div 
              class="lg:col-span-7 transition-all duration-1000"
              :class="{
                'lg:order-1': index % 2 === 1,
                'opacity-0 scale-95': activeSection !== index + 1,
                'opacity-100 scale-100 delay-300': activeSection === index + 1
              }"
            >
              <div class="relative group">
                <div class="absolute -inset-4 bg-gradient-to-r from-amber-200/40 to-orange-200/30 rounded-[2.5rem] blur-2xl opacity-50 group-hover:opacity-80 transition-opacity duration-700"></div>
                
                <div class="relative bg-white rounded-[2rem] shadow-2xl shadow-amber-900/10 border border-amber-900/5 overflow-hidden">
                  
                  <div v-if="feature.type === 'image'" class="w-full h-full relative">
                    <CompareSlider 
                      :beforeImage="feature.beforeImage" 
                      :afterImage="feature.afterImage"
                      :title="feature.shortTitle"
                      :autoAnimate="activeSection === index + 1"
                      className="w-full aspect-[4/3] object-cover"
                    />
                    <div class="absolute bottom-4 left-0 w-full text-center pointer-events-none z-10">
                      <span class="inline-block px-4 py-1.5 bg-black/40 backdrop-blur-md text-white/90 text-sm rounded-full font-medium shadow-sm border border-white/10">
                        {{ feature.demoDesc }}
                      </span>
                    </div>
                  </div>

                  <div v-else-if="feature.id === 'voice'" class="bg-gradient-to-br from-[#FFFBF0] to-[#FDFBF7] aspect-[4/3] flex flex-col justify-center items-center text-center p-12">
                    <div class="w-24 h-24 mb-8 text-amber-600 bg-white rounded-full flex items-center justify-center shadow-xl shadow-amber-100 animate-bounce-slow border border-amber-100">
                      <FontAwesomeIcon icon="fa-solid fa-microphone-lines" class="text-4xl" />
                    </div>
                    <div class="grid grid-cols-2 gap-6 w-full max-w-lg">
                      <div class="bg-white p-6 rounded-2xl border border-amber-100/50 shadow-sm hover:shadow-md transition-shadow">
                        <FontAwesomeIcon icon="fa-solid fa-keyboard" class="text-amber-400 mb-3 text-xl" />
                        <h4 class="text-base font-bold text-slate-800">文本转语音</h4>
                      </div>
                      <div class="bg-white p-6 rounded-2xl border border-amber-100/50 shadow-sm hover:shadow-md transition-shadow">
                        <FontAwesomeIcon icon="fa-solid fa-wave-square" class="text-orange-400 mb-3 text-xl" />
                        <h4 class="text-base font-bold text-slate-800">声音复活</h4>
                      </div>
                    </div>
                    <p class="mt-8 text-sm text-slate-500 font-medium">{{ feature.demoDesc }}</p>
                  </div>

                  <div v-else-if="feature.id === 'liveportrait'" class="bg-gradient-to-br from-[#FFFBF0] to-[#FDFBF7] aspect-[4/3] flex flex-col justify-center items-center text-center p-12">
                    <div class="w-24 h-24 mb-8 text-amber-600 bg-white rounded-full flex items-center justify-center shadow-xl shadow-amber-100 border border-amber-100">
                      <FontAwesomeIcon icon="fa-solid fa-video" class="text-4xl" />
                    </div>
                    <div class="flex flex-wrap gap-4 w-full justify-center max-w-lg">
                      <div class="bg-white px-6 py-3 rounded-full border border-amber-100/50 shadow-sm text-sm font-bold text-slate-700 flex items-center gap-2">
                        <FontAwesomeIcon icon="fa-solid fa-face-smile" class="text-amber-500" /> 表情生动
                      </div>
                      <div class="bg-white px-6 py-3 rounded-full border border-amber-100/50 shadow-sm text-sm font-bold text-slate-700 flex items-center gap-2">
                        <FontAwesomeIcon icon="fa-solid fa-arrows-rotate" class="text-orange-500" /> 头部动作
                      </div>
                    </div>
                    <p class="mt-8 text-sm text-slate-500 font-medium">{{ feature.demoDesc }}</p>
                  </div>

                </div>
              </div>
            </div>

          </div>
        </div>
      </section>

      <section ref="ctaSection" class="min-h-screen flex items-center justify-center relative bg-slate-900 text-white overflow-hidden">
        <div class="absolute inset-0">
          <div class="absolute top-0 left-0 w-full h-[500px] bg-gradient-to-b from-slate-800 to-transparent"></div>
          <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[1000px] h-[1000px] bg-amber-600/15 rounded-full blur-[120px] pointer-events-none"></div>
        </div>

        <div class="relative z-10 text-center px-6 max-w-4xl mx-auto w-full">
          <div 
            class="transition-all duration-1000"
            :class="activeSection === sections.length - 1 ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-12'"
          >
            <div class="mb-14">
              <span class="inline-flex items-center gap-2 px-5 py-2.5 bg-white/5 backdrop-blur-md rounded-full text-amber-200/80 font-medium text-sm border border-amber-500/20 mb-8">
                <FontAwesomeIcon icon="fa-solid fa-wand-magic-sparkles" /> 准备好让记忆重光了吗？
              </span>
              <h2 class="font-serif text-6xl md:text-[5.5rem] font-bold mb-8 leading-tight">
                立即开启您的<br/>
                <span class="text-transparent bg-clip-text bg-gradient-to-r from-amber-300 via-yellow-400 to-amber-500 italic pr-4">修复之旅</span>
              </h2>
              <p class="text-xl text-slate-400 font-light leading-relaxed max-w-2xl mx-auto">
                加入“岁月笺影”，体验前沿 AI 算法带来的极致影像复原与重构能力。
              </p>
            </div>

            <div class="flex flex-col sm:flex-row justify-center gap-6">
              <button 
                @click="goToApp"
                class="group px-12 py-5 bg-gradient-to-r from-amber-500 to-yellow-600 text-slate-900 rounded-full font-bold shadow-2xl shadow-amber-900/40 hover:scale-105 transition-all duration-300 text-lg flex items-center justify-center"
              >
                <span>{{ isLoggedIn ? '返回控制台' : '注册 / 登录系统' }}</span>
                <FontAwesomeIcon icon="fa-solid fa-arrow-right" class="ml-3 group-hover:translate-x-1 transition-transform" />
              </button>
            </div>
            
            <div class="mt-20 pt-8 border-t border-white/10 flex flex-wrap justify-center gap-8 md:gap-12 text-slate-500 text-sm">
              <span class="flex items-center gap-2"><FontAwesomeIcon icon="fa-solid fa-shield-halved" class="text-amber-600/50" /> 隐私安全保障</span>
              <span class="flex items-center gap-2"><FontAwesomeIcon icon="fa-solid fa-bolt" class="text-amber-600/50" /> 云端极速处理</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../store';
import CompareSlider from '../components/CompareSlider.vue';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';

const router = useRouter();
const authStore = useAuthStore();
const activeSection = ref(0);
const sectionRefs = ref<HTMLElement[]>([]);
const heroSection = ref<HTMLElement | null>(null);
const ctaSection = ref<HTMLElement | null>(null);

const isLoggedIn = computed(() => authStore.isAuthenticated);

// 数据配置：保持不变，调整了 badgeClass 的底色使其更温和
const features = [
  {
    id: 'time_engine',
    type: 'image',
    badge: '核心重绘',
    badgeClass: 'bg-blue-50/50 text-blue-700 border-blue-200/50',
    icon: 'fa-solid fa-hourglass-half',
    title: '时光引擎 · 智能重生',
    shortTitle: '时光引擎',
    subtitle: '基于Flux模型的AIGC智能修复，一键式解决严重破损照片，让岁月痕迹消失无踪。',
    scenes: [
      '严重破损、撕裂、霉变的老照片修复',
      '大面积褪色、模糊、失真的照片重生',
      '需要整体重构和细节重绘的珍贵照片'
    ],
    beforeImage: './assets/images/AI前.png', 
    afterImage: './assets/images/AI后.png',
    demoDesc: '拖动滑块查看：AI 如何重绘严重破损的照片',
    limitations: '时光引擎会基于AI理解进行创造性修复，对于极端破损可能与原始照片存在艺术性差异。'
  },
  {
    id: 'dustless',
    type: 'image',
    badge: '物理去瑕',
    badgeClass: 'bg-emerald-50/50 text-emerald-700 border-emerald-200/50',
    icon: 'fa-solid fa-wand-magic-sparkles',
    title: '拂尘 · 物理修复',
    shortTitle: '拂尘去瑕',
    subtitle: '像文物修复师一样，智能识别并填补岁月的缺憾，抹去折痕与污渍。',
    scenes: [
      '带有明显折痕、撕裂缝隙的老照片',
      '表面有霉斑、咖啡渍或墨水的照片',
      '扫描后带有大量灰尘噪点的底片'
    ],
    beforeImage: './assets/images/拂尘前.png', 
    afterImage: './assets/images/拂尘后.jpg',
    demoDesc: '拖动滑块查看：AI 如何无痕填补复杂的纸张裂痕',
    limitations: '对于面部五官的严重物理缺失，建议修复后结合“真容”模块进一步处理。'
  },
  {
    id: 'liuguang',
    type: 'image',
    badge: '色彩复苏',
    badgeClass: 'bg-purple-50/50 text-purple-700 border-purple-200/50',
    icon: 'fa-solid fa-palette',
    title: '流光 · 色彩复苏',
    shortTitle: '流光上色',
    subtitle: '基于深度学习的色彩分析，让记忆不再只有黑白灰，重现那个年代的温度。',
    scenes: [
      '家里的黑白老照片或底片扫描件',
      '年代久远的黑白视频截图',
      '褪色严重的彩色照片（偏红/偏黄矫正）'
    ],
    beforeImage: './assets/images/流光前.jpg', 
    afterImage: './assets/images/流光后.jpg',
    demoDesc: '智能分析衣物材质与环境光，还原最接近历史真实的色彩',
    limitations: '提供“艺术”与“纪实”两种上色模式，以适应不同历史背景下对颜色的推测。'
  },
  {
    id: 'qingying',
    type: 'image',
    badge: '画质重构',
    badgeClass: 'bg-cyan-50/50 text-cyan-700 border-cyan-200/50',
    icon: 'fa-solid fa-mountain-sun',
    title: '清影 · 画质重构',
    shortTitle: '清影超清',
    subtitle: '不仅是放大，更是重绘。利用生成式模型，让模糊的瞬间变得锐利清晰。',
    scenes: [
      '由于手抖或对焦失败导致的模糊照片',
      '早年间低像素翻盖手机拍摄的照片',
      '被微信/网络多次转发压缩的马赛克图'
    ],
    beforeImage: './assets/images/清影前.png', 
    afterImage: './assets/images/清影后.jpg',
    demoDesc: '重构发丝、衣物纹理等微小细节，分辨率瞬间提升 4 倍',
    limitations: '生成式模型对于极度模糊背景中的微小文字可能会产生推测偏差，但在静物与风景上表现极佳。'
  },
  {
    id: 'zhenrong',
    type: 'image',
    badge: '面部精修',
    badgeClass: 'bg-pink-50/50 text-pink-700 border-pink-200/50',
    icon: 'fa-regular fa-face-smile',
    title: '真容 · 肖像精修',
    shortTitle: '真容精修',
    subtitle: '穿越时空的凝视。专注于面部几何重建，找回亲人最清晰的模样。',
    scenes: [
      '五官模糊不清的大合影（看不清脸）',
      '对焦不准的人像特写',
      '面部有大量噪点或轻微破损的照片'
    ],
    beforeImage: './assets/images/真容前.png', 
    afterImage: './assets/images/真容后.jpg',
    demoDesc: '专注于眼、鼻、嘴的结构重建，显著提升五官立体感',
    limitations: '仅针对面部区域生效。如果背景也很模糊，建议先使用"清影"再用"真容"。'
  },
  {
    id: 'voice',
    type: 'audio',
    badge: '多模态语音',
    badgeClass: 'bg-indigo-50/50 text-indigo-700 border-indigo-200/50',
    icon: 'fa-solid fa-microphone',
    title: '留音 · 语音魔法',
    shortTitle: '留音语音',
    subtitle: '让照片开口说话，赋予静态图像声音的力量。支持文本转语音和声音复活。',
    scenes: [
      '为老照片添加语音描述，讲述背后故事',
      '基于少量语音样本克隆出相似的声音',
      '为家庭相册制作有声回忆录'
    ],
    demoDesc: '提供文本转语音与声音复活双模式，补齐多模态修复的重要一环。',
    limitations: '声音复活功能需要提供清晰的参考音频样本，样本质量直接影响克隆保真度。'
  },
  {
    id: 'liveportrait',
    type: 'video',
    badge: '人像复活',
    badgeClass: 'bg-teal-50/50 text-teal-700 border-teal-200/50',
    icon: 'fa-solid fa-video',
    title: '灵动 · 人像复活',
    shortTitle: '灵动人像',
    subtitle: '基于先进 AI 技术，赋予人像生动的表情和动作，重现当年的音容笑貌。',
    scenes: [
      '让老照片中的亲人动起来',
      '为历史人物照片添加生动的表情',
      '制作个性化的动态回忆录'
    ],
    demoDesc: '生成自然的头部动作、眨眼与微笑，让照片仿佛“活”了过来。',
    limitations: '处理需进行高强度计算，建议使用正面、五官清晰的人像照片以达到最佳驱动效果。'
  }
];

const sections = computed(() => [
  { name: '首页' },
  ...features.map(f => ({ name: f.shortTitle })),
  { name: '注册使用' }
]);

const scrollTo = (index: number) => {
  if (index === 0 && heroSection.value) {
    heroSection.value.scrollIntoView({ behavior: 'smooth' });
  } else if (index === sections.value.length - 1 && ctaSection.value) {
    ctaSection.value.scrollIntoView({ behavior: 'smooth' });
  } else if (sectionRefs.value[index - 1]) {
    sectionRefs.value[index - 1].scrollIntoView({ behavior: 'smooth' });
  }
};

const goToApp = () => {
  if (isLoggedIn.value) {
    router.push('/app/dashboard');
  } else {
    router.push('/login');
  }
};

const handleScroll = () => {
  const scrollPosition = window.scrollY + window.innerHeight * 0.4; 
  let current = 0;

  if (heroSection.value && scrollPosition < heroSection.value.offsetTop + heroSection.value.offsetHeight) {
    current = 0;
  } else {
    sectionRefs.value.forEach((section, index) => {
      if (section && scrollPosition >= section.offsetTop) {
        current = index + 1;
      }
    });
    if (ctaSection.value && scrollPosition >= ctaSection.value.offsetTop - window.innerHeight * 0.2) {
      current = sections.value.length - 1;
    }
  }
  activeSection.value = current;
};

const throttle = (func: Function, limit: number) => {
  let inThrottle: boolean;
  return function(this: any, ...args: any[]) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
};

onMounted(() => {
  window.addEventListener('scroll', throttle(handleScroll, 50));
  handleScroll(); 
});

onUnmounted(() => {
  window.removeEventListener('scroll', throttle(handleScroll, 50));
});
</script>

<style scoped>
html {
  scroll-behavior: smooth;
}

::-webkit-scrollbar {
  width: 8px;
}
::-webkit-scrollbar-track {
  background: #FCFBF9;
}
::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}

.animate-bounce-slow {
  animation: bounce 3s infinite;
}
</style>
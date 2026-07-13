<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';

// 定义参数接口
export interface VoiceParamsType {
  mode: 'tts' | 'clone';
  text: string;
  voiceId: string;
  refAudio?: File;
  promptText: string; // 【新增】参考样本内容
  pitch: number;
  rate: number;
}

const props = defineProps<{
  params: VoiceParamsType;
}>();

const emit = defineEmits(['update:params']);

// 本地状态同步
const localParams = ref<VoiceParamsType>({ 
  ...props.params,
  promptText: props.params.promptText || '' // 确保promptText有默认值
});
const activeTab = ref<'tts' | 'clone'>(props.params.mode);
const textLength = computed(() => localParams.value.text.length);
const promptTextLength = computed(() => localParams.value.promptText.length);

// 预设音色库 (重新配置，确保男女音色清晰区分)
const voicePresets = [
  { 
    id: 'male1', 
    name: '男一 · 沉稳磁性', 
    icon: 'fa-solid fa-user-tie', 
    desc: '沉稳磁性，中气十足，略带播音腔，适合男性语音', 
    color: 'bg-blue-500',
    demoText: '这张照片记录了我们家的美好时光，要好好珍惜这些回忆。'
  },
  { 
    id: 'male2', 
    name: '男二 · 温和亲切', 
    icon: 'fa-solid fa-user-friends', 
    desc: '温和亲切，充满亲和力，适合温和男性语音', 
    color: 'bg-indigo-500',
    demoText: '孩子，这张照片里的你多可爱啊，那时候的时光真美好。'
  },
  { 
    id: 'female1', 
    name: '女一 · 温柔细腻', 
    icon: 'fa-solid fa-user-nurse', 
    desc: '温柔细腻，清晰知性，适合女性语音', 
    color: 'bg-pink-400',
    demoText: '看着这张老照片，仿佛又回到了那个温暖的年代，真让人怀念。'
  },
  { 
    id: 'female2', 
    name: '女二 · 温暖关怀', 
    icon: 'fa-solid fa-user-nurse', 
    desc: '温暖关怀，充满关爱，适合温暖女性语音', 
    color: 'bg-rose-400',
    demoText: '宝贝，天冷了记得多穿点衣服，好好照顾自己。这张照片里的你多可爱啊。'
  },
  { 
    id: 'narrator', 
    name: '讲述者 · 标准播音', 
    icon: 'fa-solid fa-microphone-lines', 
    desc: '普通话标准，发音清晰，适合旁白和讲述', 
    color: 'bg-purple-500',
    demoText: '这是一张来自过去的照片，记录着那个年代的故事和情感。'
  }
];

// 音色预览功能 (预生成音频文件方案)
const previewAudio = ref<HTMLAudioElement | null>(null);
const isPlayingPreview = ref(false);
const currentPreviewVoice = ref<string | null>(null);

// 预生成的预览音频文件路径 (使用public目录)
const previewAudioUrls = {
  male1: '/audio/male1_preview.wav',
  male2: '/audio/male2_preview.wav',
  female1: '/audio/female1_preview.wav',
  female2: '/audio/female2_preview.wav',
  narrator: '/audio/narrator_preview.wav'
};

// 播放音色预览
const playVoicePreview = async (voiceId: string) => {
  if (isPlayingPreview.value) {
    // 如果正在播放，停止播放
    if (previewAudio.value) {
      previewAudio.value.pause();
      previewAudio.value.currentTime = 0;
    }
    isPlayingPreview.value = false;
    currentPreviewVoice.value = null;
    return;
  }
  
  const voice = voicePresets.find(v => v.id === voiceId);
  if (!voice) return;
  
  try {
    isPlayingPreview.value = true;
    currentPreviewVoice.value = voiceId;
    
    // 直接播放预生成的音频文件
    const audioUrl = previewAudioUrls[voiceId as keyof typeof previewAudioUrls];
    
    // 创建音频元素并播放
    previewAudio.value = new Audio(audioUrl);
    previewAudio.value.play();
    
    previewAudio.value.onended = () => {
      isPlayingPreview.value = false;
      currentPreviewVoice.value = null;
    };
    
    previewAudio.value.onerror = () => {
      console.error('播放预览失败:', voiceId);
      isPlayingPreview.value = false;
      currentPreviewVoice.value = null;
    };
    
  } catch (error) {
    console.error('播放预览失败:', error);
    isPlayingPreview.value = false;
    currentPreviewVoice.value = null;
  }
};

// 监听变化并回传
watch(localParams, (newVal) => {
  emit('update:params', newVal);
}, { deep: true });

// 切换模式
const setTab = (mode: 'tts' | 'clone') => {
  activeTab.value = mode;
  localParams.value.mode = mode;
};

// 触发音频上传
const fileInput = ref<HTMLInputElement | null>(null);
const triggerRefUpload = () => {
  fileInput.value?.click();
};

const handleFileChange = (e: Event) => {
  const target = e.target as HTMLInputElement;
  if (target.files?.length) {
    const file = target.files[0];
    if (file.size > 10 * 1024 * 1024) {
      alert("音频文件不能超过 10MB");
      return;
    }
    localParams.value.refAudio = file;
  }
};

const removeRefAudio = () => {
  localParams.value.refAudio = undefined;
  if (fileInput.value) fileInput.value.value = '';
};
</script>

<template>
  <div class="space-y-8 animate-fade-in pb-20">
    <!-- 模式切换 Tabs -->
    <div class="bg-gray-100 p-1.5 rounded-2xl flex relative">
      <div 
        class="absolute top-1.5 bottom-1.5 w-[calc(50%-6px)] bg-white rounded-xl shadow-sm transition-all duration-300 ease-out"
        :class="activeTab === 'tts' ? 'left-1.5' : 'left-[calc(50%+3px)]'"
      ></div>
      <button 
        v-for="mode in ['tts', 'clone']" 
        :key="mode"
        @click="setTab(mode as 'tts' | 'clone')"
        class="flex-1 relative z-10 py-2.5 text-sm font-bold transition-colors duration-300 flex items-center justify-center gap-2"
        :class="activeTab === mode ? 'text-emerald-600' : 'text-gray-500 hover:text-gray-700'"
      >
        <FontAwesomeIcon :icon="mode === 'tts' ? 'fa-solid fa-font' : 'fa-solid fa-fingerprint'" />
        {{ mode === 'tts' ? '文本转语音' : '声音复活' }}
      </button>
    </div>

    <!-- TTS 模式内容 -->
    <transition name="fade" mode="out-in">
      <div v-if="activeTab === 'tts'" class="space-y-6">
        <div>
          <label class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-2">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> 选择预设音色
          </label>
          <div class="grid grid-cols-1 gap-3">
            <div 
              v-for="voice in voicePresets" 
              :key="voice.id"
              class="relative p-3 rounded-xl border-2 transition-all cursor-pointer flex items-center gap-3 group"
              :class="localParams.voiceId === voice.id 
                ? 'border-emerald-500 bg-emerald-50/50 shadow-sm' 
                : 'border-transparent bg-white hover:bg-gray-50 hover:border-gray-200'"
            >
              <div 
                class="w-10 h-10 rounded-full flex items-center justify-center text-lg transition-colors text-white shadow-sm"
                :class="voice.color"
              >
                <FontAwesomeIcon :icon="voice.icon" />
              </div>
              <div class="flex-1" @click="localParams.voiceId = voice.id">
                <div class="font-bold text-gray-800 text-sm">{{ voice.name }}</div>
                <div class="text-xs text-gray-400 mt-0.5">{{ voice.desc }}</div>
              </div>
              <div class="flex items-center gap-2">
                <button 
                  @click.stop="playVoicePreview(voice.id)"
                  class="w-8 h-8 rounded-full flex items-center justify-center transition-all hover:scale-110"
                  :class="currentPreviewVoice === voice.id && isPlayingPreview 
                    ? 'bg-red-100 text-red-500' 
                    : 'bg-gray-100 text-gray-500 hover:bg-emerald-100 hover:text-emerald-500'"
                >
                  <FontAwesomeIcon 
                    :icon="currentPreviewVoice === voice.id && isPlayingPreview ? 'fa-solid fa-stop' : 'fa-solid fa-play'" 
                    class="text-xs"
                  />
                </button>
                <div v-if="localParams.voiceId === voice.id" class="text-emerald-500">
                  <FontAwesomeIcon icon="fa-solid fa-circle-check" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 克隆模式内容 -->
      <div v-else class="space-y-6">
        <div>
          <label class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-2">
            <span class="w-1.5 h-1.5 rounded-full bg-indigo-500"></span> 上传声音样本
          </label>
          
          <input type="file" ref="fileInput" class="hidden" accept="audio/*" @change="handleFileChange">

          <div v-if="!localParams.refAudio" 
            @click="triggerRefUpload"
            class="border-2 border-dashed border-gray-300 rounded-2xl p-6 flex flex-col items-center justify-center text-gray-400 hover:border-indigo-400 hover:text-indigo-500 hover:bg-indigo-50/30 transition-all cursor-pointer group h-32"
          >
            <div class="w-12 h-12 rounded-full bg-gray-100 group-hover:bg-white flex items-center justify-center mb-3 transition-colors shadow-sm">
              <FontAwesomeIcon icon="fa-solid fa-cloud-arrow-up" class="text-lg" />
            </div>
            <span class="text-sm font-medium">点击上传录音文件</span>
            <span class="text-xs mt-1 opacity-60">支持 MP3/WAV (3-10秒最佳)</span>
          </div>

          <div v-else class="bg-white border border-gray-200 rounded-2xl p-4 shadow-sm relative overflow-hidden group">
            <div class="absolute top-0 left-0 w-1 h-full bg-indigo-500 transition-all group-hover:w-1.5"></div>
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-indigo-100 text-indigo-500 flex items-center justify-center shrink-0">
                <FontAwesomeIcon icon="fa-solid fa-file-audio" />
              </div>
              <div class="flex-1 min-w-0">
                <div class="text-sm font-bold text-gray-800 truncate">{{ localParams.refAudio.name }}</div>
                <div class="text-xs text-gray-400">{{ (localParams.refAudio.size / 1024 / 1024).toFixed(2) }} MB</div>
              </div>
              <button @click="removeRefAudio" class="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-full transition-colors">
                <FontAwesomeIcon icon="fa-solid fa-trash" />
              </button>
            </div>
          </div>
          
          <p class="text-[10px] text-gray-400 leading-relaxed bg-gray-50 p-3 rounded-lg border border-gray-100">
            <FontAwesomeIcon icon="fa-solid fa-circle-info" class="mr-1" />
            建议上传干声（无背景音乐、无噪音）的音频，时长 5 秒左右效果最佳。
          </p>
        </div>

        <!-- 【新增】参考样本内容输入 -->
        <div>
          <div class="flex justify-between items-center mb-3">
            <label class="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center gap-2">
              <span class="w-1.5 h-1.5 rounded-full bg-indigo-500"></span> 
              参考样本内容
            </label>
            <span class="text-xs font-mono font-medium" :class="promptTextLength > 50 ? 'text-red-500' : 'text-gray-400'">
              {{ promptTextLength }}/50
            </span>
          </div>
          <div class="relative group">
            <textarea
              v-model="localParams.promptText"
              class="w-full h-20 p-4 bg-gray-50 border-0 rounded-2xl text-sm focus:ring-2 focus:ring-indigo-500/20 focus:bg-white transition-all resize-none placeholder-gray-400"
              placeholder="请输入参考音频中实际说的话..."
              maxlength="50"
            ></textarea>
            <div class="absolute bottom-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity">
              <FontAwesomeIcon icon="fa-solid fa-pen" class="text-gray-300 text-xs" />
            </div>
          </div>
          <p class="text-[10px] text-gray-600 leading-relaxed bg-emerald-50 p-3 rounded-lg border border-emerald-100 mt-2">
            <FontAwesomeIcon icon="fa-solid fa-circle-exclamation" class="mr-1 text-emerald-500" />
            <strong>重要：</strong>请准确填写参考音频中实际说的话，必须与音频内容<strong>完全一致</strong>，这是确保克隆成功的关键！
          </p>
        </div>
      </div>
    </transition>

    <!-- 公共：文本输入 -->
    <div>
      <div class="flex justify-between items-center mb-3">
        <label class="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center gap-2">
          <span class="w-1.5 h-1.5 rounded-full bg-gray-400"></span> 
          {{ activeTab === 'tts' ? '想说的话' : '复活台词' }}
        </label>
        <span class="text-xs font-mono font-medium" :class="textLength > 300 ? 'text-red-500' : 'text-gray-400'">
          {{ textLength }}/300
        </span>
      </div>
      <div class="relative group">
        <textarea
          v-model="localParams.text"
          class="w-full h-32 p-4 bg-gray-50 border-0 rounded-2xl text-sm focus:ring-2 focus:ring-emerald-500/20 focus:bg-white transition-all resize-none placeholder-gray-400"
          :placeholder="activeTab === 'tts' ? '输入您想转换的文字...' : '输入您希望人物说出的话...'"
        ></textarea>
        <div class="absolute bottom-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity">
           <FontAwesomeIcon icon="fa-solid fa-pen" class="text-gray-300 text-xs" />
        </div>
      </div>
    </div>

    <!-- 公共：语速控制 -->
    <div>
      <div class="flex justify-between items-center mb-3">
        <label class="text-xs font-bold text-gray-400 uppercase tracking-wider">语速调整</label>
        <span class="text-xs font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-100">
          {{ localParams.rate > 0 ? '+' : ''}}{{ localParams.rate }}%
        </span>
      </div>
      <input 
        type="range" 
        v-model.number="localParams.rate" 
        min="-50" max="50" step="10"
        class="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-emerald-500"
      />
      <div class="flex justify-between text-[10px] text-gray-400 mt-2 font-medium">
        <span>慢速</span>
        <span>标准</span>
        <span>快速</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.animate-fade-in {
  animation: fadeIn 0.4s ease-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
<script setup lang="ts">
import { ref, watch, onMounted, computed, onUnmounted, nextTick } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { MODULES, API_BASE_URL } from '../constants';
import { api, getFullImageUrl } from '../services/api';
import ImageCompare from '../components/ImageCompare.vue';
import BrushCanvas from '../components/BrushCanvas.vue';
import EmotionalLoader from '../components/EmotionalLoader.vue';
import { defineComponent, h } from 'vue';
import { ModuleStep } from '../types';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';

// 导入模块参数组件
import DustlessParams from '../components/modules/DustlessParams.vue';
import LiuguangParams from '../components/modules/LiuguangParams.vue';
import QingyingParams from '../components/modules/QingyingParams.vue';
import ZhenrongParams from '../components/modules/ZhenrongParams.vue';
// 导入声音参数组件
import VoiceParams, { VoiceParamsType } from '../components/modules/VoiceParams.vue';
// 导入灵动·人像复活参数组件
import LivePortraitParams, { LivePortraitParamsType } from '../components/modules/LivePortraitParams.vue';
// 导入灵动·人像复活视频展示组件
import LivePortraitVideo from '../components/modules/LivePortraitVideo.vue';
// 导入时光引擎参数组件
import TimeEngineParams from '../components/modules/TimeEngineParams.vue';



const route = useRoute();
const router = useRouter();
const selectedPhotoUrl = ref<string | null>(null);
const selectedPhotoId = ref<number | null>(null);
const isProcessing = ref(false);
const resultImage = ref<string | null>(null);
const fileInput = ref<HTMLInputElement | null>(null);
const loadingMsg = ref('');
const livePortraitProgress = ref(0);
const timeEngineResults = ref<string[]>([]); // 时光引擎多图结果
const timeEngineProgress = ref(0); // 时光引擎进度

// 模块状态持久化键名
const MODULE_STORAGE_KEY = 'workshop_module_states';

// 保存模块状态到localStorage
const saveModuleState = () => {
    const moduleState = {
        moduleId: moduleId.value,
        selectedPhotoUrl: selectedPhotoUrl.value,
        selectedPhotoId: selectedPhotoId.value,
        resultImage: resultImage.value,
        timeEngineResults: timeEngineResults.value,
        livePortraitProgress: livePortraitProgress.value,
        timeEngineProgress: timeEngineProgress.value,
        voiceParams: voiceParams.value,
        livePortraitParams: livePortraitParams.value,
        savedAt: Date.now()
    };
    
    try {
        localStorage.setItem(MODULE_STORAGE_KEY, JSON.stringify(moduleState));
    } catch (error) {
        console.warn('保存模块状态失败:', error);
    }
};

// 恢复模块状态从localStorage
const restoreModuleState = () => {
    try {
        const savedState = localStorage.getItem(MODULE_STORAGE_KEY);
        if (savedState) {
            const state = JSON.parse(savedState);
            
            // 只恢复当前模块的状态
            if (state.moduleId === moduleId.value) {
                selectedPhotoUrl.value = state.selectedPhotoUrl;
                selectedPhotoId.value = state.selectedPhotoId;
                resultImage.value = state.resultImage;
                timeEngineResults.value = state.timeEngineResults || [];
                livePortraitProgress.value = state.livePortraitProgress || 0;
                timeEngineProgress.value = state.timeEngineProgress || 0;
                
                // 恢复模块特定参数
                if (isVoiceModule.value && state.voiceParams) {
                    voiceParams.value = { ...voiceParams.value, ...state.voiceParams };
                }
                if (isLivePortraitModule.value && state.livePortraitParams) {
                    livePortraitParams.value = { ...livePortraitParams.value, ...state.livePortraitParams };
                }
                
                console.log('模块状态已恢复');
            }
        }
    } catch (error) {
        console.warn('恢复模块状态失败:', error);
    }
};

// 清除模块状态
const clearModuleState = () => {
    try {
        localStorage.removeItem(MODULE_STORAGE_KEY);
    } catch (error) {
        console.warn('清除模块状态失败:', error);
    }
};

// ---------------------- 声音模块逻辑 Start ----------------------

// 声音参数状态
const voiceParams = ref<VoiceParamsType>({
  mode: 'tts',
  text: '',
  voiceId: 'zh-CN-YunzeNeural',
  refAudio: undefined,
  pitch: 0,
  rate: 0
});

// 处理声音生成
const handleVoiceProcess = async () => {
    // 验证输入
    if (!voiceParams.value.text.trim()) {
        alert("请输入要生成的文字内容");
        return;
    }

    if (voiceParams.value.text.length > 1000) {
        alert("文本内容过长，请控制在1000字以内");
        return;
    }

    if (voiceParams.value.mode === 'clone' && !voiceParams.value.refAudio) {
        alert("请先上传参考声音样本");
        return;
    }

    // 声音克隆模式特殊处理
    if (voiceParams.value.mode === 'clone') {
        const confirmClone = confirm("声音克隆需要启动专门的AI服务，可能需要较长时间，是否继续？");
        if (!confirmClone) {
            return;
        }
    }

    isProcessing.value = true;
    // 声音模块我们复用 resultImage 变量来存储生成的音频 URL
    resultImage.value = null; 

    try {
        const formData = new FormData();
        formData.append('text', voiceParams.value.text.trim());
        formData.append('mode', voiceParams.value.mode);
        
        // 语速调整格式："+10%" 或 "-10%"
        const rateStr = voiceParams.value.rate >= 0 
            ? `+${voiceParams.value.rate}%` 
            : `${voiceParams.value.rate}%`;
        formData.append('rate', rateStr);

        // 根据模式添加不同参数
        if (voiceParams.value.mode === 'tts') {
            formData.append('voice_id', voiceParams.value.voiceId);
        } else if (voiceParams.value.refAudio) {
            formData.append('ref_audio', voiceParams.value.refAudio);
            // 关键修复：添加prompt_text参数
            if (voiceParams.value.promptText) {
                formData.append('prompt_text', voiceParams.value.promptText);
            }
        }

        // 显示处理状态
        const processingText = voiceParams.value.mode === 'clone' 
            ? '正在进行声音克隆，请耐心等待...' 
            : '正在合成语音...';
        
        // 调用后端音频生成接口
        const response = await fetch(`${API_BASE_URL}/workshop/voice/generate`, {
            method: 'POST',
            body: formData,
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
            },
        });

        if (!response.ok) {
            const error = await response.json();
            
            // 特殊处理声音克隆错误
            if (voiceParams.value.mode === 'clone' && response.status === 503) {
                throw new Error("声音克隆服务暂时不可用，请稍后重试");
            }
            
            throw new Error(error.detail || '生成失败');
        }

        const blob = await response.blob();
        
        // 验证音频数据
        if (blob.size === 0) {
            throw new Error("生成的音频数据无效");
        }

        const audioUrl = URL.createObjectURL(blob);
        
        // 创建音频元素进行预览
        const audio = new Audio(audioUrl);
        audio.oncanplaythrough = () => {
            // 音频加载完成，显示结果
            resultImage.value = audioUrl;
            isProcessing.value = false;
        };
        
        audio.onerror = () => {
            throw new Error("音频文件格式错误");
        };
        
        // 设置超时处理 - 根据模式设置不同超时时间
        const timeoutDuration = voiceParams.value.mode === 'clone' ? 180000 : 90000; // 克隆模式3分钟，TTS模式1.5分钟
        setTimeout(() => {
            if (isProcessing.value) {
                isProcessing.value = false;
                alert(`音频生成超时（${voiceParams.value.mode === 'clone' ? '3分钟' : '1.5分钟'}），请重试`);
            }
        }, timeoutDuration);

    } catch (e: any) {
        console.error("声音生成错误:", e);
        isProcessing.value = false;
        
        // 更友好的错误提示
        let errorMessage = `声音生成失败: ${e.message}`;
        
        if (e.message.includes("网络")) {
            errorMessage = "网络连接失败，请检查网络设置";
        } else if (e.message.includes("超时")) {
            errorMessage = "生成超时，请稍后重试";
        } else if (e.message.includes("服务不可用")) {
            errorMessage = "AI服务暂时不可用，请稍后重试";
        }
        
        alert(errorMessage);
    }
};
// ---------------------- 声音模块逻辑 End ----------------------

// ---------------------- 灵动·人像复活模块逻辑 Start ----------------------
// 处理灵动·人像复活返回
const handleLivePortraitBack = () => {
    // 重置处理状态和结果
    isProcessing.value = false;
    resultImage.value = null;
    livePortraitProgress.value = 0;
    loadingMsg.value = '';
    
    console.log('返回参数设置界面');
}

// 处理灵动·人像复活生成
const handleLivePortraitProcess = async () => {
    // 验证输入
    if (!selectedPhotoUrl.value && !selectedPhotoId.value) {
        alert("请先选择或上传一张照片！");
        return;
    }

    if (!livePortraitParams.value.drivingAudio) {
        alert("请先上传驱动音频");
        return;
    }

    isProcessing.value = true;
    loadingMsg.value = '正在让照片开口说话...';
    resultImage.value = null;
    livePortraitProgress.value = 0;

    try {
        const formData = new FormData();
        
        // 添加图片数据
        if (selectedPhotoId.value) {
            formData.append('image_id', selectedPhotoId.value.toString());
        } else if (rawFile.value) {
            formData.append('image', rawFile.value);
        }
        
        // 添加音频数据
        formData.append('audio', livePortraitParams.value.drivingAudio);
        
        // 添加驱动视频数据（视频驱动模式必须）
        if (livePortraitParams.value.drivingVideo) {
            formData.append('driving_video', livePortraitParams.value.drivingVideo);
        }
        
        formData.append('relative_motion', livePortraitParams.value.relativeMotion.toString());
        formData.append('paste_back', livePortraitParams.value.pasteBack.toString());
        formData.append('expression_scale', livePortraitParams.value.expressionScale.toString());
        
        // 调用API创建任务
        const response = await fetch(`${API_BASE_URL}/workshop/live_portrait/generate`, {
            method: 'POST',
            body: formData,
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
            },
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '任务创建失败');
        }

        const result = await response.json();
        const taskId = result.task_id;
        
        // 发送任务开始事件到创作时光轴 - 使用更可靠的事件触发
        const taskData = {
          id: Date.now().toString(),
          operation_type: operationType,
          task_id: taskId
        };
        
        // 方法1：直接发送事件
        window.dispatchEvent(new CustomEvent('time_trace_task_start', {
          detail: { taskData }
        }));
        
        // 方法2：保存到本地存储作为备用方案
        savePendingTask(taskData);
        
        // 轮询任务状态
        let taskCompleted = false;
        let pollCount = 0;
        const maxPollCount = 420; // 最多轮询420秒（7分钟，每秒一次）
        
        while (!taskCompleted && pollCount < maxPollCount) {
            await new Promise(resolve => setTimeout(resolve, 1000)); // 每秒轮询一次
            
            const statusResponse = await fetch(`${API_BASE_URL}/workshop/tasks/${taskId}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
                },
            });
            
            if (statusResponse.ok) {
                const taskData = await statusResponse.json();
                
                if (taskData.status === 'completed') {
                    taskCompleted = true;
                    
                    // 获取生成的视频URL
                    if (taskData.result_path) {
                        // 关键修复：使用getFullImageUrl函数处理路径，避免重复static前缀
                        const videoUrl = getFullImageUrl(taskData.result_path);
                        resultImage.value = videoUrl;
                        
                        // 保存模块状态
                        saveModuleState();
                        
                        alert('人像复活完成！');
                    } else {
                        throw new Error('任务完成但未生成结果文件');
                    }
                } else if (taskData.status === 'failed') {
                    throw new Error(taskData.error_message || '任务处理失败');
                }
                
                // 更新进度信息 - 修复进度条波动问题
                loadingMsg.value = `正在生成人像动画... (${pollCount + 1}/420秒)`;
                // 使用线性进度计算，避免波动
                const baseProgress = Math.min((pollCount / maxPollCount) * 100, 100);
                // 添加小幅度随机波动，但保持整体稳定前进
                const smoothProgress = baseProgress + (Math.random() * 2 - 1); // ±1%的随机波动
                livePortraitProgress.value = Math.max(0, Math.min(smoothProgress, 100));
            } else {
                throw new Error('获取任务状态失败');
            }
            
            pollCount++;
        }
        
        if (!taskCompleted) {
            // 420秒（7分钟）超时后提供更友好的处理选项
            const userChoice = confirm('人像动画生成已超过7分钟，通常需要更多时间完成。\n\n选择"确定"继续等待，或"取消"停止生成。\n\n建议：如果网络良好，可以继续等待；如果网络较慢，建议稍后重试。');
            
            if (userChoice) {
                // 用户选择继续等待，延长轮询时间
                loadingMsg.value = '继续等待生成完成...';
                
                // 继续轮询，但不再限制时间
                while (!taskCompleted) {
                    await new Promise(resolve => setTimeout(resolve, 2000)); // 每2秒轮询一次
                    
                    const statusResponse = await fetch(`${API_BASE_URL}/workshop/tasks/${taskId}`, {
                        headers: {
                            'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
                        },
                    });
                    
                    if (statusResponse.ok) {
                        const taskData = await statusResponse.json();
                        
                        if (taskData.status === 'completed') {
                            taskCompleted = true;
                            const videoUrl = taskData.result?.video_url;
                            if (videoUrl) {
                                resultImage.value = videoUrl;
                                alert('人像复活完成！');
                            } else {
                                throw new Error('任务完成但未生成结果文件');
                            }
                        } else if (taskData.status === 'failed') {
                            throw new Error(taskData.error_message || '任务处理失败');
                        }
                        
                        loadingMsg.value = '继续等待生成完成...';
                    } else {
                        throw new Error('获取任务状态失败');
                    }
                }
            } else {
                // 用户选择取消
                throw new Error('生成已取消，您可以稍后重试');
            }
        }
        
    } catch (e: any) {
        console.error("人像复活生成错误:", e);
        
        // 更友好的错误提示
        let errorMessage = `人像复活失败: ${e.message}`;
        
        if (e.message.includes("网络")) {
            errorMessage = "网络连接失败，请检查网络设置";
        } else if (e.message.includes("超时")) {
            errorMessage = "生成超时，请稍后重试";
        } else if (e.message.includes("服务不可用")) {
            errorMessage = "AI服务暂时不可用，请稍后重试";
        } else if (e.message.includes("生成已取消")) {
            errorMessage = "生成已取消，您可以稍后重试";
        }
        
        alert(errorMessage);
    } finally {
        isProcessing.value = false;
    }
};
const livePortraitParams = ref<LivePortraitParamsType>({
  drivingAudio: null,
  relativeMotion: true,
  pasteBack: true,
  expressionScale: 1.0
});
// ---------------------- 灵动·人像复活模块逻辑 End ----------------------

// 触发上传
const triggerUpload = () => {
  fileInput.value?.click();
};

// 处理拖放
const handleDrop = (event: DragEvent) => {
  const files = event.dataTransfer?.files;
  if (files && files.length > 0) {
    handleFileSelect({ target: { files } } as unknown as Event);
  }
};

// 处理文件选择
const handleFileSelect = async (event: Event) => {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;

  // 前端文件格式验证
  const allowedExtensions = ['jpg', 'jpeg', 'png', 'gif', 'mp4', 'mov', 'avi', 'webm'];
  const fileExtension = file.name.split('.').pop()?.toLowerCase();
  
  if (!fileExtension || !allowedExtensions.includes(fileExtension)) {
    const supportedFormats = allowedExtensions.map(ext => ext.toUpperCase()).join(', ');
    alert(`❌ 文件格式不支持！\n\n当前文件格式: ${fileExtension || '未知'}\n支持的文件格式: ${supportedFormats}\n\n请选择支持的格式重新上传。`);
    target.value = '';
    return;
  }

  // 文件大小验证 (100MB限制)
  const maxSize = 100 * 1024 * 1024; // 100MB
  if (file.size > maxSize) {
    const fileSizeMB = (file.size / (1024 * 1024)).toFixed(1);
    alert(`❌ 文件过大！\n\n当前文件大小: ${fileSizeMB}MB\n最大支持大小: 100MB\n\n请选择较小的文件重新上传。`);
    target.value = '';
    return;
  }

  // 保存原始文件对象给API用
  rawFile.value = file;

  // 检测文件类型并通知流光模块
  const isVideoFile = file.type.startsWith('video/');
  if (isColorizeModule.value && liuguangParamsRef.value) {
      nextTick(() => {
          liuguangParamsRef.value?.handleFileTypeChange(isVideoFile);
      });
  }

  try {
      const photo = await api.uploadPhoto(file);
      selectedPhotoId.value = photo.id;
      selectedPhotoUrl.value = photo.url || '';
      resultImage.value = null;
      maskData.value = null;
      maskId.value = null;
  } catch (e: any) {
      // 精准的错误提示
      let errorMessage = "上传失败";
      
      if (e.response?.status === 413) {
        errorMessage = "❌ 文件过大！服务器拒绝接收。请选择小于100MB的文件。";
      } else if (e.response?.status === 415) {
        errorMessage = `❌ 文件格式不支持！\n\n当前文件格式: ${fileExtension}\n支持的文件格式: JPG, JPEG, PNG, GIF, MP4, MOV, AVI, WEBM\n\n请选择支持的格式重新上传。`;
      } else if (e.message?.includes('network') || e.message?.includes('Network')) {
        errorMessage = "❌ 网络连接失败！请检查网络连接后重试。";
      } else if (e.message?.includes('timeout')) {
        errorMessage = "❌ 上传超时！请检查网络连接或稍后重试。";
      }
      
      alert(errorMessage);
      console.error("文件上传失败详情:", e);
  } finally {
    // 清空文件输入，允许重新选择相同的文件
    if (target) {
      target.value = '';
    }
  }
};

// 修复模式
const repairMode = ref<'auto' | 'manual' | 'denoise'>('auto');
// 掩码数据
const maskData = ref<string | null>(null);
const maskId = ref<number | null>(null);
const isMaskUploading = ref(false);
// 原始文件对象，用于API调用
const rawFile = ref<File | null>(null);

// 拂尘修复参数
const dustlessParams = ref({
  detectThreshold: 0.3, // 检测灵敏度
  dilateLevel: 2,       // Mask加粗等级
});

// 流光修复参数（适配DDColor模型）
const colorizeParams = ref({
  modelSize: 'advanced',    // 模型大小：统一为高级模型
  inputSize: 512,        // 输入尺寸：128-1024
  colorEnhance: true,    // 是否进行颜色增强
  prompt: '',            // 多模态提示词
  enhance_only: false    // 仅增强模式
});

// 保存原始修复结果，用于增强后的回退功能
const originalResultImage = ref(null);

// 清影修复参数
const qingyingParams = ref({
  prompt: "",           // 修复提示词
  upscale: 1,           // 放大倍数：1, 2, 4, 8
  patchSize: 512,       // Patch大小：512, 640, 768, 896, 1024
  stride: 256,          // Stride：256, 320, 384, 448, 512
  seed: Math.floor(Math.random() * 4294967296),  // 随机种子：0到2^32-1之间的随机数
  enhanceText: true,    // 是否增强文字清晰度
  repairBackground: true // 是否修复背景细节
});

// 真容修复参数
const zhenrongParams = ref({
  faceEnhanceLevel: 5,  // 面部增强程度：1-10
  skinSmooth: 50,       // 皮肤平滑度：0-100%
  eyeEnhance: true,     // 是否增强眼睛
  lipEnhance: true      // 是否增强嘴唇
});

// 模块参数组件引用
const liuguangParamsRef = ref<InstanceType<typeof LiuguangParams> | null>(null);

// 媒体类型选择状态
const selectedMediaType = ref<'image' | 'video'>('image');

const moduleId = computed(() => route.params.moduleId as string);
const moduleConfig = computed(() => MODULES.find((m) => m.id === moduleId.value));

// 判断当前是否为拂尘修复模块
const isDustlessModule = computed(() => moduleId.value === ModuleStep.DUSTLESS);
// 判断当前是否为流光修复模块
const isColorizeModule = computed(() => moduleId.value === ModuleStep.LIUGUANG);
// 判断当前是否为清影修复模块
const isQingyingModule = computed(() => moduleId.value === ModuleStep.QINGYING);
// 判断当前是否为声音模块
const isVoiceModule = computed(() => moduleId.value === ModuleStep.VOICE);
// 判断当前是否为灵动·人像复活模块
const isLivePortraitModule = computed(() => moduleId.value === ModuleStep.LIVE_PORTRAIT);
// 判断当前是否为时光引擎模块
const isTimeEngineModule = computed(() => moduleId.value === ModuleStep.TIME_ENGINE);

// 判断当前选中的文件是否为视频
const isVideo = computed(() => {
    if (!rawFile.value && !selectedPhotoUrl.value) return false;
    
    // 如果有原始文件，检查文件类型
    if (rawFile.value) {
        return rawFile.value.type.startsWith('video/');
    }
    
    // 如果是URL，检查文件扩展名
    if (selectedPhotoUrl.value) {
        const url = selectedPhotoUrl.value.toLowerCase();
        return ['.mp4', '.mov', '.avi', '.webm'].some(ext => url.endsWith(ext));
    }
    
    return false;
});

// Icon Wrapper Component for Vue
const IconWrapper = defineComponent({
  props: ['icon'],
  setup(props) {
    return () => props.icon;
  }
});

// Update state when route/query changes
watch(() => route.query, (newQuery) => {
    if (newQuery.id) {
        const id = parseInt(newQuery.id as string);
        selectedPhotoId.value = isNaN(id) ? null : id;
        console.log('Selected photo ID:', selectedPhotoId.value);
    }
    
    // 处理从图库页面传递过来的照片URL
    if (newQuery.photo) {
        selectedPhotoUrl.value = newQuery.photo as string;
        console.log('Selected photo URL:', selectedPhotoUrl.value);
    }
}, { immediate: true });

watch(moduleId, () => {
    // Reset when module changes
    resultImage.value = null;
    isProcessing.value = false;
    repairMode.value = 'auto';
    maskData.value = null;
    maskId.value = null;
    selectedMediaType.value = 'image'; // 重置媒体类型选择
    // 声音模块不需要重置 selectedPhotoUrl，因为它们不互通，但可以清空
    if (isVoiceModule.value) {
        selectedPhotoUrl.value = null;
    }
});



// 上传掩码
const uploadMask = async () => {
    if (!maskData.value || !selectedPhotoId.value) return;
    
    isMaskUploading.value = true;
    
    try {
        // 将base64转换为Blob
        const blob = await fetch(maskData.value).then(res => res.blob());
        const file = new File([blob], 'mask.png', { type: 'image/png' });
        
        // 上传掩码
        const formData = new FormData();
        formData.append('mask', file);
        formData.append('photo_id', selectedPhotoId.value.toString());
        
        // 调用API上传掩码
        const response = await fetch(`${API_BASE_URL}/workshop/masks`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
            },
            body: formData
        });
        
        if (!response.ok) {
            // 尝试重新登录
            if (response.status === 401) {
                console.error('认证失败，尝试重新登录');
                router.push('/login');
                return;
            }
            throw new Error('掩码上传失败');
        }
        
        const result = await response.json();
        maskId.value = result.id;
        
        console.log('掩码上传成功:', result);
        // 上传成功提示
        alert('掩码上传成功！现在可以点击修复按钮进行修复了。');
        
    } catch (e) {
        console.error('掩码上传失败:', e);
        alert('掩码上传失败，请稍后重试');
    } finally {
        isMaskUploading.value = false;
    }
};

// 开始修复
const handleProcess = async () => {
    // =======================================================
    // 🌟 核心拦截：如果是时光引擎，走专属的高级 API，不走旧任务队列
    // =======================================================
    if (moduleId.value === 'time_engine') {
        isProcessing.value = true;
        resultImage.value = null;
        timeEngineProgress.value = 0;
        
        try {
            // 1. 获取当前选中的图片
            let imageFile = rawFile.value;
            let imageUrl = selectedPhotoUrl.value;
            
            // 如果没有原始文件但有图片URL，将URL转换为File对象
            if (!imageFile && imageUrl) {
                console.log("🚀 时光引擎启动：从URL转换图片文件");
                const imgResponse = await fetch(imageUrl);
                const blob = await imgResponse.blob();
                imageFile = new File([blob], 'time_engine_target.jpg', { type: 'image/jpeg' });
            }
            
            if (!imageFile) {
                throw new Error("没有可用的图片文件");
            }
            
            // 2. 静默检测 ConfUI 服务状态（不显示弹窗）
            console.log("🔍 检测 ConfUI 服务状态...");
            try {
                const confuiStatusResponse = await fetch('http://127.0.0.1:8188/', { 
                    method: 'GET', 
                    timeout: 5000 
                });
                if (!confuiStatusResponse.ok) {
                    console.warn("⚠️ ConfUI 服务异常，但继续尝试处理");
                } else {
                    console.log("✅ ConfUI 服务正常");
                }
            } catch (confuiError) {
                console.warn("⚠️ ConfUI 服务检测失败，但继续尝试处理:", confuiError);
            }
            
            console.log("🚀 时光引擎点火！通过 workshop 模块创建任务");
            
            // 3. 点火！通过 workshop 模块创建时光引擎任务
            // 使用认证的 API 客户端，避免 401 错误
            const taskData = await api.createTask(
                'time_engine',
                imageFile,
                undefined, // 提示词
                {}, // 时光引擎不需要额外参数
                undefined, // 掩码ID
                true, // usePowerPaint
                'object-removal', // taskType
                'auto' // 修复模式
            );
            
            const taskId = taskData.id;
            
            console.log("✅ 时光引擎任务创建成功，Task ID:", taskId);

            // 4. 开启全息雷达：每 5 秒轮询一次任务进度，支持600秒超长等待
            let pollCount = 0;
            const maxPollCount = 120; // 600秒 / 5秒 = 120次轮询
            
            const pollInterval = setInterval(async () => {
                try {
                    // 使用认证的 API 客户端查询任务状态
                    const taskInfo = await api.getTask(taskId);
                    
                    // 找到当前时光引擎任务
                    const currentTask = taskInfo;
                    
                    if (!currentTask) {
                        throw new Error("未找到时光引擎任务");
                    }

                    // 更新进度条 - 基于轮询次数计算进度
                    pollCount++;
                    const baseProgress = Math.min((pollCount / maxPollCount) * 100, 100);
                    // 添加小幅度随机波动，但保持整体稳定前进
                    const smoothProgress = baseProgress + (Math.random() * 2 - 1); // ±1%的随机波动
                    timeEngineProgress.value = Math.max(0, Math.min(smoothProgress, 100));

                    if (currentTask.status === 'completed') {
                        // 引擎处理完毕！
                        clearInterval(pollInterval);
                        isProcessing.value = false;
                        
                        // 【修复】使用统一的URL拼接函数
                        const getFullUrl = (path: string) => {
                            if (!path) return '';
                            // 如果已经是完整 URL (http开头)，直接返回
                            if (path.startsWith('http://') || path.startsWith('https://')) {
                                return path;
                            }
                            // 使用统一的getFullImageUrl函数处理路径
                            return getFullImageUrl(path);
                        };
                        
                        if (currentTask.step_results && currentTask.step_results.length > 0) {
                            // 【修复】使用统一的URL拼接函数
                            timeEngineResults.value = currentTask.step_results.map(path => {
                                return getFullImageUrl(path);
                            });

                            // 第一张图作为主图
                            resultImage.value = timeEngineResults.value[0];
                            
                            console.log("🎉 时光引擎处理完成！共生成", timeEngineResults.value.length, "张图片");
                            
                        } else if (currentTask.result_path) {
                            // 【修复】使用统一的URL拼接函数
                            resultImage.value = getFullImageUrl(currentTask.result_path);
                            console.log("🎉 时光引擎处理完成！单图结果:", resultImage.value);
                        }
                        
                        // 保存模块状态
                        saveModuleState();
                        
                    } else if (currentTask.status === 'failed') {
                        clearInterval(pollInterval);
                        isProcessing.value = false;
                        console.error('引擎执行失败:', currentTask.error_message);
                        alert(`时光引擎执行失败: ${currentTask.error_message}`);
                    }
                } catch(e) {
                    console.error("轮询进度出错:", e);
                    // 不立即停止轮询，而是记录错误并继续尝试
                    console.warn("轮询遇到网络波动，继续尝试...");
                }
            }, 5000);

            // 5. 设置900秒超时保护
            const timeoutDuration = 900000; // 900秒 = 15分钟
            const timeoutId = setTimeout(() => {
                clearInterval(pollInterval);
                if (isProcessing.value) {
                    isProcessing.value = false;
                    const userChoice = confirm('时光引擎处理已超过15分钟，通常需要更多时间完成。\n\n选择"确定"继续等待，或"取消"停止生成。\n\n建议：如果网络良好，可以继续等待；如果网络较慢，建议稍后重试。');
                    
                    if (userChoice) {
                        // 用户选择继续等待，重新启动轮询
                        isProcessing.value = true;
                        const extendedPollInterval = setInterval(async () => {
                            try {
                                const taskInfo = await api.getTask(taskId);
                                const currentTask = taskInfo;
                                
                                if (currentTask?.status === 'completed') {
                                    clearInterval(extendedPollInterval);
                                    isProcessing.value = false;
                                    
                                    if (currentTask.step_results && currentTask.step_results.length > 0) {
                                        resultImage.value = currentTask.step_results[0].startsWith('/') ? 
                                            `http://localhost:8000${currentTask.step_results[0]}` : 
                                            `http://localhost:8000/static/${currentTask.step_results[0]}`;
                                        timeEngineResults.value = currentTask.step_results.map(path => 
                                            path.startsWith('/') ? 
                                            `http://localhost:8000${path}` : 
                                            `http://localhost:8000/static/${path}`
                                        );
                                    } else if (currentTask.result_path) {
                                        resultImage.value = currentTask.result_path.startsWith('/') ? 
                                            `http://localhost:8000${currentTask.result_path}` : 
                                            `http://localhost:8000/static/${currentTask.result_path}`;
                                    }
                                } else if (currentTask?.status === 'failed') {
                                    clearInterval(extendedPollInterval);
                                    isProcessing.value = false;
                                    alert(`时光引擎执行失败: ${currentTask.error_message}`);
                                }
                            } catch(e) {
                                console.warn("扩展轮询遇到网络波动，继续尝试...");
                            }
                        }, 5000);
                    }
                }
            }, timeoutDuration);

            // 清理函数
            onUnmounted(() => {
                clearInterval(pollInterval);
                clearTimeout(timeoutId);
            });

        } catch (error: any) {
            console.error('时光引擎唤醒失败', error);
            isProcessing.value = false;
            
            // 精准的错误提示分类处理
            let errorMessage = "时光引擎启动失败";
            let detailedMessage = error.message || "未知错误";
            
            // 根据错误类型提供精准提示
            if (error.message?.includes('HTTPConnectionPool') || error.message?.includes('10061')) {
                errorMessage = "❌ ConfUI服务未启动！"
                detailedMessage = "时光引擎依赖的AI计算服务(ConfUI)未启动或连接失败。\n\n请检查：\n1. ConfUI服务是否已启动\n2. 端口8188是否被占用\n3. 网络连接是否正常\n\n启动ConfUI服务后重新尝试。";
            } else if (error.message?.includes('网络') || error.message?.includes('连接') || error.message?.includes('Network')) {
                errorMessage = "❌ 网络连接异常！"
                detailedMessage = "网络连接失败，请检查：\n1. 后端服务是否正常运行\n2. 网络连接是否稳定\n3. 防火墙设置是否正确\n\n请检查网络后重新尝试。";
            } else if (error.message?.includes('401') || error.message?.includes('认证')) {
                errorMessage = "❌ 用户认证失败！"
                detailedMessage = "用户认证失败，请重新登录系统。";
            } else if (error.message?.includes('500') || error.message?.includes('服务器')) {
                errorMessage = "❌ 后端服务异常！"
                detailedMessage = "后端服务出现异常，请联系管理员检查服务状态。";
            } else if (error.message?.includes('ConfUI') || error.message?.includes('ComfyUI')) {
                errorMessage = "❌ AI计算服务异常！"
                detailedMessage = "AI计算服务(ConfUI)配置异常，请确认：\n1. ConfUI服务已正确安装\n2. 相关模型文件已下载\n3. 服务端口配置正确\n\n请联系管理员检查ConfUI服务配置。";
            } else if (error.message?.includes('超时') || error.message?.includes('timeout')) {
                errorMessage = "❌ 请求超时！"
                detailedMessage = "请求处理超时，请检查：\n1. 网络连接是否稳定\n2. 服务器负载是否过高\n3. 文件大小是否过大\n\n请稍后重试或联系管理员。";
            } else if (error.response?.status === 413) {
                errorMessage = "❌ 文件过大！"
                detailedMessage = "上传的文件过大，超过服务器限制。\n\n请选择小于100MB的文件重新上传。";
            } else if (error.response?.status === 415) {
                errorMessage = "❌ 文件格式不支持！"
                detailedMessage = "上传的文件格式不被支持。\n\n支持的文件格式：JPG, JPEG, PNG, GIF, MP4, MOV, AVI, WEBM\n请选择支持的格式重新上传。";
            }
            
            alert(`${errorMessage}\n\n${detailedMessage}`);
        }
        
        // 【极度关键】：拦截成功，直接 return 退出，千万别往下走旧代码！
        return;
    }
    // =======================================================
    
    // 如果是声音模块则不执行
    if (isVoiceModule.value) {
        return handleVoiceProcess();
    }
    
    // 如果是灵动·人像复活模块，则执行特殊处理
    if (isLivePortraitModule.value) {
        return handleLivePortraitProcess();
    }
    
    // 检查是否有原始文件对象或已选择的照片ID
    if ((!rawFile.value && !selectedPhotoId.value) || !moduleId.value) {
        alert("请先选择图片！");
        return;
    }
    
    isProcessing.value = true;
    resultImage.value = null;
    
    try {
        // 如果是手动修复模式，先上传掩码并等待完成
        if (isDustlessModule.value && repairMode.value === 'manual' && maskData.value) {
            console.log("🚀 开始上传掩码...");
            await uploadMask();
            console.log("✅ 掩码上传完成，maskId:", maskId.value);
            
            // 验证maskId是否已正确设置
            if (!maskId.value) {
                throw new Error("掩码上传失败，未获取到有效的maskId");
            }
        }
        
        // 获取当前选中的模块ID
        const moduleIdVal = moduleId.value;
        let newTask;
        
        // 根据用户选择的方式调用不同的API
        if (rawFile.value) {
            // 直接上传的图片，使用FormData API
            console.log("正在调用API, 模块:", moduleIdVal, "文件:", rawFile.value.name);
            
            // 根据模块类型传递不同的参数
            let params = null;
            console.log("模块判断调试: isDustlessModule=", isDustlessModule.value, "isColorizeModule=", isColorizeModule.value, "isQingyingModule=", isQingyingModule.value);
            console.log("当前模块ID:", moduleIdVal);
            
            if (isDustlessModule.value) {
                params = dustlessParams.value;
                console.log("拂尘修复参数:", params);
            } else if (isColorizeModule.value) {
                params = colorizeParams.value;
                console.log("流光修复参数:", params);
            } else if (isQingyingModule.value) {
                params = qingyingParams.value;
                console.log("清影修复参数:", params);
            }
            
            console.log("最终传递的参数:", params);
            console.log("传递的maskId:", repairMode.value === 'manual' ? maskId.value : undefined);
            
            newTask = await api.createTask(
                moduleIdVal,
                rawFile.value,
                undefined,
                params,
                repairMode.value === 'manual' ? maskId.value : undefined,
                undefined,
                undefined,
                repairMode.value
            );
        } else if (selectedPhotoId.value) {
            // 从图库选择的图片，使用JSON API
            console.log("正在从图库调用API, 模块:", moduleIdVal, "照片ID:", selectedPhotoId.value);
            
            // 根据模块类型传递不同的参数
            let params = null;
            console.log("图库路径-模块判断调试: isDustlessModule=", isDustlessModule.value, "isColorizeModule=", isColorizeModule.value, "isQingyingModule=", isQingyingModule.value);
            console.log("图库路径-当前模块ID:", moduleIdVal);
            
            if (isDustlessModule.value) {
                params = dustlessParams.value;
                console.log("图库路径-拂尘修复参数:", params);
            } else if (isColorizeModule.value) {
                params = colorizeParams.value;
                console.log("图库路径-流光修复参数:", params);
            } else if (isQingyingModule.value) {
                params = qingyingParams.value;
                console.log("图库路径-清影修复参数:", params);
            }
            
            console.log("图库路径-最终传递的参数:", params);
            console.log("图库路径-传递的maskId:", repairMode.value === 'manual' ? maskId.value : undefined);
            
            newTask = await api.createTaskFromGallery(
                selectedPhotoId.value,
                moduleIdVal,
                params,
                repairMode.value === 'manual' ? maskId.value : undefined,
                undefined,
                undefined,
                repairMode.value
            );
        } else {
            throw new Error("没有可用的图片数据");
        }
        
        const poll = async () => {
            try {
                console.log('开始轮询任务状态，任务ID:', newTask.id);
                const taskInfo = await api.getTask(newTask.id);
                
                // 添加详细的调试日志
                console.log('接收到的任务状态:', taskInfo.status);
                console.log('接收到的任务结果路径:', taskInfo.result_path);
                console.log('完整的任务信息:', JSON.stringify(taskInfo, null, 2));
                
                // 无论结果如何，只要状态是completed或failed，就结束处理状态
                if (taskInfo.status === 'completed' || taskInfo.status === 'failed') {
                    console.log('任务状态是completed或failed，准备更新UI');
                    
                    if (taskInfo.status === 'completed') {
                        console.log('任务完成，准备显示结果');
                        
                        // 即使没有result_path，也要结束处理状态
                        if (taskInfo.result_path) {
                            console.log('有结果路径，设置resultImage:', taskInfo.result_path);
                            
                            // 使用getFullImageUrl函数处理结果路径，确保URL格式正确
                            resultImage.value = getFullImageUrl(taskInfo.result_path);
                            
                            console.log('构造的完整图片URL:', resultImage.value);
                        } else {
                            console.warn('任务完成但没有结果路径');
                            resultImage.value = '';
                        }
                        
                        alert('修复完成！');
                    } else if (taskInfo.status === 'failed') {
                        console.log('任务失败');
                        // 设置isProcessing为false
                        isProcessing.value = false;
                        alert(`修复失败: ${taskInfo.error_message || '未知错误'}`);
                    }
                    
                    // 强制更新isProcessing状态
                    console.log('将isProcessing从', isProcessing.value, '设置为false');
                    isProcessing.value = false;
                    console.log('更新后的isProcessing:', isProcessing.value);
                } else {
                    console.log('任务仍在处理中，状态:', taskInfo.status, '，1.5秒后再次轮询');
                    setTimeout(poll, 1500);
                }
            } catch (e: any) {
                console.error('轮询任务失败:', e);
                console.error('错误详情:', JSON.stringify(e, null, 2));
                
                // 不要结束处理状态，继续轮询
                console.log('轮询失败，1.5秒后再次尝试');
                setTimeout(poll, 1500);
            }
        };
        poll();
    } catch (e) {
        console.error(e);
        isProcessing.value = false;
        alert("无法创建任务，请稍后重试");
    }
};

// 切换修复模式
const toggleRepairMode = () => {
  if (repairMode.value === 'auto') {
    repairMode.value = 'manual';
  } else if (repairMode.value === 'manual') {
    repairMode.value = 'denoise';
  } else {
    repairMode.value = 'auto';
  }
  
  // 切换模式时重置掩码（仅自动和降噪模式不需要掩码）
  if (repairMode.value === 'auto' || repairMode.value === 'denoise') {
    maskData.value = null;
    maskId.value = null;
  }
};

// 处理掩码变化
const handleMaskChange = (mask: string) => {
    maskData.value = mask;
};

// 保存掩码
const saveMask = (mask: string) => {
    maskData.value = mask;
    uploadMask();
};

// 重置
const reset = () => {
    // 如果是音频，清理 URL
    if (isVoiceModule.value && resultImage.value) {
        URL.revokeObjectURL(resultImage.value);
    }
    resultImage.value = null;
    maskData.value = null;
    maskId.value = null;
    
    // 清除模块状态
    clearModuleState();
    
    console.log('模块状态已重置');
};

// 继续修复
const continueRepair = async () => {
    if (!resultImage.value) return;
    
    try {
        // 直接继续修复，不需要确认对话框
        // 显示加载状态
        isProcessing.value = true;
        loadingMsg.value = '正在准备继续修复...';
        
        // 从修复结果URL创建File对象
        const response = await fetch(resultImage.value);
        if (!response.ok) {
            throw new Error(`获取修复结果失败: ${response.status} ${response.statusText}`);
        }
        
        const blob = await response.blob();
        
        // 智能检测文件类型
        let fileType = 'image/jpeg';
        let fileExtension = '.jpg';
        
        if (blob.type.includes('png')) {
            fileType = 'image/png';
            fileExtension = '.png';
        } else if (blob.type.includes('gif')) {
            fileType = 'image/gif';
            fileExtension = '.gif';
        }
        
        // 生成唯一文件名
        const timestamp = Date.now();
        const filename = `continued_repair_${timestamp}${fileExtension}`;
        
        // 创建File对象
        const file = new File([blob], filename, { type: fileType });
        
        // 将当前修复结果作为新的输入图片
        selectedPhotoUrl.value = resultImage.value;
        // 重要修复：保留原始照片ID，以便后续手动修复时能够正确上传掩码
        // selectedPhotoId.value = null; // 不再清除原照片ID
        rawFile.value = file; // 设置新的文件对象
        
        // 重置修复结果和相关状态
        resultImage.value = null;
        maskData.value = null;
        maskId.value = null;
        
        // 显示成功消息
        setTimeout(() => {
            isProcessing.value = false;
            loadingMsg.value = '';
            alert('继续修复准备完成！现在您可以调整参数进行进一步修复。');
        }, 500);
        
    } catch (error) {
        console.error('继续修复失败:', error);
        isProcessing.value = false;
        loadingMsg.value = '';
        alert(`继续修复失败: ${error.message || '请稍后重试'}`);
    }
};



// 下载结果 - 智能识别照片和视频格式（使用Blob转换强制下载）
const downloadResult = async () => {
    if (!resultImage.value) return;
    
    try {
        // 方案A：使用Blob转换方案（强制下载，避免预览）
        const response = await fetch(resultImage.value);
        if (!response.ok) throw new Error('网络响应错误');
        
        const blob = await response.blob();
        const blobUrl = window.URL.createObjectURL(blob);
        
        // 智能判断文件类型
        let fileExtension = '.jpg';
        let fileName = `restored_${moduleConfig.value?.id}`;
        
        // 根据模块类型和文件内容判断格式
        if (isLivePortraitModule.value) {
            // 灵动模块总是视频格式
            fileExtension = '.mp4';
            fileName = `liveportrait_video`;
        } else if (isVideo.value) {
            // 其他模块的视频文件
            fileExtension = '.mp4';
        } else if (blob.type.startsWith('video/')) {
            // 根据blob类型判断
            fileExtension = '.mp4';
        } else if (blob.type.startsWith('audio/')) {
            // 声音模块
            fileExtension = '.mp3';
            fileName = `restored_voice`;
        } else if (blob.type.includes('png')) {
            // PNG格式
            fileExtension = '.png';
        } else {
            // 默认图片格式
            fileExtension = '.jpg';
        }
        
        // 添加时间戳确保文件名唯一
        const timestamp = new Date().getTime();
        
        const link = document.createElement('a');
        link.href = blobUrl;
        link.download = `${fileName}_${timestamp}${fileExtension}`;
        
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        
        document.body.removeChild(link);
        window.URL.revokeObjectURL(blobUrl);
        
    } catch (error) {
        console.error('Blob下载失败，尝试降级方案:', error);
        
        // 方案B：降级处理 - 直接下载（依赖浏览器对同源的判断）
        try {
            const timestamp = new Date().getTime();
            
            const link = document.createElement('a');
            link.href = resultImage.value;
            link.download = `restored_${moduleConfig.value?.id}_${timestamp}.jpg`;
            link.target = '_blank'; // 如果下载失败，至少会在新标签页打开
            
            link.style.display = 'none';
            document.body.appendChild(link);
            link.click();
            
            // 延迟清理，确保点击事件完成
            setTimeout(() => {
                document.body.removeChild(link);
            }, 100);
            
            console.log("尝试触发下载，如未弹出保存对话框，请在新页面右键另存为");
            
        } catch (fallbackError) {
            console.error('降级方案也失败:', fallbackError);
            
            // 方案C：最终降级 - 直接打开图片
            window.open(resultImage.value, '_blank');
            alert('下载失败，文件已在新标签页打开，请右键选择"另存为..."进行保存。');
        }
    }
};

// 增强色彩
const enhanceColor = async () => {
    if (!resultImage.value) return;
    
    try {
        isProcessing.value = true;
        
        // 在增强前保存原始修复结果
        originalResultImage.value = resultImage.value;
        
        // 获取当前修复结果作为输入
        const response = await fetch(resultImage.value);
        const blob = await response.blob();
        const file = new File([blob], 'colorized_image.jpg', { type: 'image/jpeg' });
        
        // 使用现有的createTask方法创建增强任务
        const moduleIdVal = moduleId.value;
        const newTask = await api.createTask(
            moduleIdVal,
            file,
            undefined,
            { ...colorizeParams.value, enhance_only: true } // 仅增强模式
        );
        
        // 轮询任务状态
        const poll = async () => {
            try {
                const taskInfo = await api.getTask(newTask.id);
                
                if (taskInfo.status === 'completed' || taskInfo.status === 'failed') {
                    if (taskInfo.status === 'completed') {
                        if (taskInfo.result_path) {
                            // 更新结果图片
                            resultImage.value = getFullImageUrl(taskInfo.result_path);
                            alert('色彩增强完成！');
                        } else {
                            alert('色彩增强完成但没有结果图片');
                        }
                    } else if (taskInfo.status === 'failed') {
                        alert(`色彩增强失败: ${taskInfo.error_message || '未知错误'}`);
                    }
                    
                    isProcessing.value = false;
                } else {
                    // 1.5秒后再次轮询
                    setTimeout(poll, 1500);
                }
            } catch (error) {
                console.error('轮询任务状态失败:', error);
                alert('轮询任务状态失败，请稍后重试');
                isProcessing.value = false;
            }
        };
        
        // 开始轮询
        poll();
        
    } catch (error) {
        console.error('色彩增强失败:', error);
        alert('色彩增强失败，请稍后重试');
        isProcessing.value = false;
    }
};

// 回退色彩增强
const undoColorEnhance = () => {
    if (!originalResultImage.value) return;
    
    // 将结果图片恢复到增强前的状态
    resultImage.value = originalResultImage.value;
    
    // 清除保存的原始结果
    originalResultImage.value = null;
    
    alert('已回退到增强前的状态！');
};

// 保存待处理任务到本地存储
const savePendingTask = (taskData: any) => {
  try {
    const pendingTasks = localStorage.getItem('time_trace_pending_tasks');
    let tasks = [];
    
    if (pendingTasks) {
      tasks = JSON.parse(pendingTasks);
    }
    
    // 添加新任务
    tasks.push(taskData);
    
    // 保存到本地存储
    localStorage.setItem('time_trace_pending_tasks', JSON.stringify(tasks));
    
    console.log('待处理任务已保存:', taskData);
  } catch (error) {
    console.error('保存待处理任务失败:', error);
  }
};

// 文本识别
const handleTextRecognition = async () => {
    if (!selectedPhotoId.value) {
        alert('请先选择或上传一张照片');
        return;
    }
    
    try {
        isProcessing.value = true;
        loadingMsg.value = '正在识别图像文字...';
        
        // 调用文本识别API
        const result = await api.recognizeText(selectedPhotoId.value);
        
        if (result.text) {
            // 将识别到的文本填充到提示词中
            qingyingParams.value.prompt = `清晰修复包含"${result.text}"文字的照片，增强文字清晰度，修复背景细节`;
        } else {
            alert('未识别到文字');
        }
    } catch (e) {
        console.error('文本识别失败:', e);
        alert('文本识别失败，请稍后重试');
    } finally {
        isProcessing.value = false;
    }
};

// 替换图片功能
const replaceImage = () => {
  // 创建文件输入元素
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = 'image/*';
  input.style.display = 'none';
  
  input.onchange = (e) => {
    const target = e.target as HTMLInputElement;
    const file = target.files?.[0];
    if (file) {
      // 验证文件类型
      if (!file.type.startsWith('image/')) {
        alert('请选择图片文件');
        return;
      }
      
      // 调用现有的文件处理逻辑
      handleLocalFileUpload(e);
    }
  };
  
  document.body.appendChild(input);
  input.click();
  document.body.removeChild(input);
};

// 图片缩放功能
const zoomImage = (imageUrl: string, title: string) => {
  // 创建全屏图片查看器
  const overlay = document.createElement('div');
  overlay.className = 'fixed inset-0 bg-black/90 z-40 flex items-center justify-center p-4';
  
  const container = document.createElement('div');
  container.className = 'relative max-w-full max-h-full';
  
  const img = document.createElement('img');
  img.src = imageUrl;
  img.className = 'max-w-full max-h-full object-contain rounded-lg';
  img.alt = title;
  
  const closeBtn = document.createElement('button');
  closeBtn.className = 'absolute top-4 right-4 w-10 h-10 bg-white text-gray-800 rounded-full flex items-center justify-center hover:bg-gray-200 transition-colors shadow-lg';
  closeBtn.innerHTML = '<i class="fa-solid fa-xmark text-lg"></i>';
  closeBtn.onclick = () => {
    document.body.removeChild(overlay);
  };
  
  const titleEl = document.createElement('div');
  titleEl.className = 'absolute top-4 left-4 bg-black/50 text-white px-3 py-1 rounded-full text-sm';
  titleEl.textContent = title;
  
  container.appendChild(img);
  container.appendChild(closeBtn);
  container.appendChild(titleEl);
  overlay.appendChild(container);
  
  // 点击背景关闭
  overlay.onclick = (e) => {
    if (e.target === overlay) {
      document.body.removeChild(overlay);
    }
  };
  
  // ESC键关闭
  const handleKeydown = (e: KeyboardEvent) => {
    if (e.key === 'Escape') {
      document.body.removeChild(overlay);
      document.removeEventListener('keydown', handleKeydown);
    }
  };
  
  document.addEventListener('keydown', handleKeydown);
  document.body.appendChild(overlay);
};

// 切换时光引擎结果
const switchTimeEngineResult = (index: number) => {
  if (timeEngineResults.value && timeEngineResults.value.length > index) {
    resultImage.value = timeEngineResults.value[index];
    console.log("切换时光引擎结果到方案", index + 1);
  }
};

// 处理图片下载 - 智能降级方案
const handleImageDownload = async (imageUrl: string) => {
  try {
    // 方案A：尝试使用Blob转换方案（最佳体验）
    const response = await fetch(imageUrl);
    if (!response.ok) throw new Error('网络响应错误');
    
    const blob = await response.blob();
    const blobUrl = window.URL.createObjectURL(blob);
    
    let fileExtension = '.jpg';
    let fileName = `restored_${moduleConfig.value?.id}_${Date.now()}`;
    
    // 根据模块类型和文件内容判断格式
    if (isLivePortraitModule.value) {
      // 灵动模块总是视频格式
      fileExtension = '.mp4';
    } else if (blob.type.includes('video')) {
      fileExtension = '.mp4';
    } else if (blob.type.includes('png')) {
      fileExtension = '.png';
    } else if (blob.type.includes('gif')) {
      fileExtension = '.gif';
    }

    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = `${fileName}${fileExtension}`;
    
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    
    document.body.removeChild(link);
    window.URL.revokeObjectURL(blobUrl);
    
  } catch (error) {
    console.error('Blob下载失败，尝试降级方案:', error);
    
    // 方案B：降级处理 - 直接下载（依赖浏览器对同源的判断）
    try {
      let fileExtension = '.jpg';
      let fileName = `restored_${moduleConfig.value?.id}_${Date.now()}`;
      
      const link = document.createElement('a');
      link.href = imageUrl;
      link.download = `${fileName}${fileExtension}`;
      link.target = '_blank'; // 如果下载失败，至少会在新标签页打开
      
      link.style.display = 'none';
      document.body.appendChild(link);
      link.click();
      
      // 延迟清理，确保点击事件完成
      setTimeout(() => {
        document.body.removeChild(link);
      }, 100);
      
      console.log("尝试触发下载，如未弹出保存对话框，请在新页面右键另存为");
      
    } catch (fallbackError) {
      console.error('降级方案也失败:', fallbackError);
      
      // 方案C：最终降级 - 直接打开图片
      window.open(imageUrl, '_blank');
      alert('下载失败，图片已在新标签页打开，请右键选择"图片另存为..."进行保存。');
    }
  }
};

// 清空照片功能
const clearPhoto = () => {
  if (confirm('确定要清空当前照片吗？这将重置当前模块的所有状态。')) {
    selectedPhotoUrl.value = null;
    selectedPhotoId.value = null;
    resultImage.value = null;
    maskData.value = null;
    maskId.value = null;
    
    // 清除模块状态
    clearModuleState();
    
    console.log('照片已清空，模块状态已重置');
  }
};

const triggerLocalUpload = () => {
  fileInput.value?.click();
};

const handleLocalFileUpload = async (event: Event) => {
    const target = event.target as HTMLInputElement;
    const file = target.files?.[0];
    if (!file) return;

    // 保存原始文件对象给API用
    rawFile.value = file;

    // 检测文件类型并通知流光模块
    const isVideoFile = file.type.startsWith('video/');
    if (isColorizeModule.value && liuguangParamsRef.value) {
        nextTick(() => {
            liuguangParamsRef.value?.handleFileTypeChange(isVideoFile);
        });
    }

    try {
        const photo = await api.uploadPhoto(file);
        selectedPhotoId.value = photo.id;
        selectedPhotoUrl.value = photo.url || '';
        resultImage.value = null;
        maskData.value = null;
        maskId.value = null;
        
        // 保存模块状态
        saveModuleState();
    } catch (e) {
        alert("上传失败");
    }
};

// 组件挂载时恢复模块状态
onMounted(() => {
    // 检查URL参数中是否有历史记录ID
    const historyId = route.query.history_id as string;
    
    if (historyId) {
        // 如果有历史记录ID，加载对应的历史记录
        loadHistoryData(parseInt(historyId));
    } else {
        // 否则恢复模块状态
        setTimeout(() => {
            restoreModuleState();
        }, 100);
    }
});

// 加载历史记录数据
const loadHistoryData = async (historyId: number) => {
    try {
        console.log('开始加载历史记录，ID:', historyId);
        const histories = await api.getHistories();
        console.log('获取到的历史记录数量:', histories.length);
        
        const targetHistory = histories.find(h => h.id === historyId);
        
        if (targetHistory) {
            console.log('找到目标历史记录:', {
                id: targetHistory.id,
                operation_type: targetHistory.operation_type,
                input_url: targetHistory.input_url,
                result_url: targetHistory.result_url
            });
            
            // 设置修复完成状态
            selectedPhotoUrl.value = targetHistory.input_url; // 修复前的图片
            selectedPhotoId.value = targetHistory.id;
            resultImage.value = targetHistory.result_url; // 修复后的图片
            
            // 对于时光引擎模块，需要设置timeEngineResults
            if (targetHistory.operation_type === 'time_engine') {
                timeEngineResults.value = [targetHistory.result_url];
                console.log('设置时光引擎结果:', timeEngineResults.value);
            }
            
            // 对于灵动模块，需要设置处理完成状态
            if (targetHistory.operation_type.includes('live_portrait')) {
                isProcessing.value = false;
                livePortraitProgress.value = 100;
                console.log('设置灵动模块完成状态');
            }
            
            console.log('已加载历史记录并设置修复完成状态:', targetHistory.operation_type);
            console.log('selectedPhotoUrl:', selectedPhotoUrl.value);
            console.log('resultImage:', resultImage.value);
        } else {
            console.log('未找到对应的历史记录，ID:', historyId);
            restoreModuleState();
        }
    } catch (error) {
        console.error('加载历史记录失败:', error);
        // 失败时恢复模块状态
        restoreModuleState();
    }
};
</script>

<template>
  <div v-if="moduleConfig" class="flex h-screen bg-[#FDFCFB] overflow-hidden">
    
    <!-- 引入动态加载器: 传入自定义文字 -->
    <!-- 在LivePortrait模块中隐藏EmotionalLoader，避免重复加载界面 -->
    <EmotionalLoader
      v-if="!isLivePortraitModule"
      :module="moduleConfig"
      :show="isProcessing"
      :loading-text="isVoiceModule ? (voiceParams.mode === 'clone' ? '正在进行声纹克隆与合成...' : '正在合成自然语音...') : undefined"
    />

    <!-- 左侧：沉浸式画布区 (占用大部分空间) -->
    <div class="flex-1 relative flex flex-col min-w-0 bg-[#F3F4F6]">
      <!-- 顶部工具条 -->
      <div class="absolute top-4 left-4 right-4 z-10 flex justify-between items-center pointer-events-none">
        <div class="bg-white/80 backdrop-blur shadow-sm rounded-full px-4 py-2 pointer-events-auto flex items-center gap-2">
          <button @click="router.back()" class="w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-100 transition text-gray-600">
            <FontAwesomeIcon icon="fa-solid fa-arrow-left" />
          </button>
          <span class="text-sm font-medium text-gray-700 border-l border-gray-300 pl-3 ml-1">{{ moduleConfig.name }}</span>
        </div>
        
        <!-- 统一的操作按钮组 -->
        <div class="pointer-events-auto flex gap-4 items-center">
          <!-- 图片操作按钮 (非声音模块显示) -->
          <div v-if="selectedPhotoUrl && !isVoiceModule" class="flex gap-3">
            <button 
              @click="clearPhoto"
              class="bg-white/80 backdrop-blur shadow-sm px-5 py-2 rounded-full text-sm text-gray-600 hover:bg-gray-50 transition flex items-center gap-2"
            >
              <FontAwesomeIcon icon="fa-solid fa-trash" /> 清空
            </button>
            <button 
              @click="replaceImage"
              class="bg-white/80 backdrop-blur shadow-sm px-5 py-2 rounded-full text-sm text-gray-600 hover:bg-gray-50 transition flex items-center gap-2"
            >
              <FontAwesomeIcon icon="fa-solid fa-rotate" /> 替换
            </button>
            <button 
              v-if="resultImage"
              @click="zoomImage(selectedPhotoUrl, '原图')"
              class="bg-white/80 backdrop-blur shadow-sm px-5 py-2 rounded-full text-sm text-gray-600 hover:bg-gray-50 transition flex items-center gap-2"
            >
              <FontAwesomeIcon icon="fa-solid fa-expand" /> 原图
            </button>
            <button 
              v-if="resultImage"
              @click="zoomImage(resultImage, '修复结果')"
              class="bg-white/80 backdrop-blur shadow-sm px-5 py-2 rounded-full text-sm text-gray-600 hover:bg-gray-50 transition flex items-center gap-2"
            >
              <FontAwesomeIcon icon="fa-solid fa-expand" /> 结果
            </button>
          </div>
          
          <!-- 声音模块的操作按钮 (仅在生成结果后) -->
          <div v-if="isVoiceModule && resultImage" class="flex gap-3">
            <button @click="reset" class="bg-white/80 backdrop-blur shadow-sm px-5 py-2 rounded-full text-sm text-gray-600 hover:bg-gray-50 transition flex items-center gap-2">
              <FontAwesomeIcon icon="fa-solid fa-rotate-left" /> 重置
            </button>
          </div>

          <!-- 通用下载按钮 (智能适配照片/视频/音频) -->
          <div v-if="resultImage && !isVoiceModule" class="flex gap-3">
            <button @click="reset" class="bg-white/80 backdrop-blur shadow-sm px-5 py-2 rounded-full text-sm text-gray-600 hover:bg-gray-50 transition flex items-center gap-2">
              <FontAwesomeIcon icon="fa-solid fa-rotate-left" /> 重置
            </button>
            <!-- 继续修复按钮 (仅拂尘模块显示) -->
            <button v-if="isDustlessModule" @click="continueRepair" class="bg-blue-500 text-white shadow-lg px-6 py-2 rounded-full text-sm font-medium hover:bg-blue-600 transition flex items-center gap-2">
              <FontAwesomeIcon icon="fa-solid fa-arrow-rotate-right" /> 继续修复
            </button>
            <button @click="downloadResult" class="bg-gray-900 text-white shadow-lg px-6 py-2 rounded-full text-sm font-medium hover:bg-black transition flex items-center gap-2">
              <FontAwesomeIcon :icon="isLivePortraitModule ? 'fa-solid fa-video' : 'fa-solid fa-download'" /> 
              {{ isLivePortraitModule ? '保存视频' : '保存图片' }}
            </button>
          </div>
        </div>
      </div>

      <!-- 画布核心内容 -->
      <div class="flex-1 flex items-center justify-center p-8 select-none">
        
        <!-- ================= 声音模块 UI ================= -->
        <div v-if="isVoiceModule" class="w-full h-full flex items-center justify-center">
            
            <!-- 状态 A: 结果展示 (音频播放器) -->
            <div v-if="resultImage" class="bg-white/90 backdrop-blur-xl rounded-[2.5rem] p-12 shadow-2xl shadow-emerald-200/50 w-full max-w-2xl text-center relative overflow-hidden group animate-fade-in">
                <!-- 装饰背景 -->
                <div class="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-emerald-500 via-teal-500 to-cyan-500"></div>
                <div class="absolute -bottom-20 -right-20 w-64 h-64 bg-emerald-500/10 rounded-full blur-3xl group-hover:bg-emerald-500/20 transition-colors duration-700"></div>
                <div class="absolute -top-20 -left-20 w-64 h-64 bg-teal-500/10 rounded-full blur-3xl group-hover:bg-teal-500/20 transition-colors duration-700"></div>

                <div class="w-24 h-24 mx-auto bg-gradient-to-br from-emerald-100 to-teal-50 rounded-full flex items-center justify-center mb-8 shadow-inner relative">
                    <div class="absolute inset-0 rounded-full border border-emerald-200 animate-ping opacity-20"></div>
                    <FontAwesomeIcon icon="fa-solid fa-volume-high" class="text-4xl text-emerald-600" />
                </div>
                
                <h3 class="text-2xl font-serif font-bold text-gray-800 mb-2">声音已复活</h3>
                <p class="text-gray-400 text-sm mb-8 font-light">点击下方播放器试听，或下载保存</p>
                
                <!-- HTML5 Audio -->
                <audio :src="resultImage" controls class="w-full mb-10 outline-none custom-audio block"></audio>

                <div class="flex gap-4 justify-center">
                    <button @click="reset" class="px-6 py-3 rounded-xl text-gray-500 hover:bg-gray-100 transition font-medium text-sm">
                        重新生成
                    </button>
                    <a :href="resultImage" download="voice_restored.mp3" class="px-8 py-3 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white shadow-lg shadow-emerald-500/30 transition transform hover:-translate-y-0.5 font-bold flex items-center gap-2 text-sm">
                        <FontAwesomeIcon icon="fa-solid fa-download" /> 下载音频
                    </a>
                </div>
            </div>

            <!-- 状态 B: 初始引导 -->
            <div v-else class="text-center opacity-60">
                <div class="w-64 h-64 mx-auto mb-6 bg-gradient-to-tr from-gray-100 to-white rounded-full flex items-center justify-center shadow-inner border border-gray-100">
                    <FontAwesomeIcon icon="fa-solid fa-microphone-lines" class="text-8xl text-gray-200" />
                </div>
                <h2 class="text-2xl font-serif text-gray-800 mb-2">声音复活工坊</h2>
                <p class="text-base text-gray-400">请在右侧面板配置音色与台词，重现记忆中的声音</p>
            </div>
        </div>

        <!-- ================= 图像模块 UI (原有逻辑) ================= -->
        <div v-else class="w-full h-full flex items-center justify-center">
          
          <!-- ================= 时光引擎专属时空穿梭界面 ================= -->
          <template v-if="isTimeEngineModule">
            <!-- 1. 空状态：时空之门 -->
            <div v-if="!selectedPhotoUrl" class="absolute inset-0 flex items-center justify-center stargate-container overflow-hidden">
              <!-- 时空隧道特效 -->
              <div class="stargate-tunnel">
                <div class="stargate-ring"></div>
                <div class="stargate-ring"></div>
                <div class="stargate-ring"></div>
                <div class="stargate-ring"></div>
              </div>
              
              <!-- 核心时空坐标 -->
              <div 
                class="relative z-10 w-80 h-80 rounded-full border border-white/60 bg-white/40 backdrop-blur-md shadow-[0_0_50px_rgba(212,175,55,0.3)] flex flex-col items-center justify-center cursor-pointer transition-transform duration-700 hover:scale-110 core-hover"
                @click="triggerUpload"
                @dragover.prevent
                @drop.prevent="handleDrop"
              >
                <!-- 旋转光环 -->
                <div class="absolute inset-2 border-[2px] border-[#d4af37]/30 rounded-full border-dashed animate-[spin_20s_linear_infinite]"></div>
                
                <!-- 能量核心 -->
                <div class="w-16 h-16 bg-gradient-to-br from-[#d4af37] to-[#f9e0a2] rounded-full shadow-[0_0_30px_rgba(212,175,55,0.8)] animate-pulse flex items-center justify-center mb-6">
                  <FontAwesomeIcon icon="fa-solid fa-compass" class="text-2xl text-[#0a0806] drop-shadow-[0_0_10px_rgba(212,175,55,0.8)]" />
                </div>
                
                <h2 class="text-2xl font-bold tracking-[0.3em] text-[#b8860b] mb-2 drop-shadow-[0_0_10px_rgba(212,175,55,0.5)]">开启时空穿梭</h2>
                <p class="text-xs text-[#8a7f6d] tracking-[0.1em]">拖曳或点击 注入影像坐标</p>
              </div>
              
              <!-- 隐藏的文件输入框 -->
              <input type="file" ref="fileInput" class="hidden" accept="image/*" @change="handleFileSelect">
            </div>

            <!-- 2. 处理中状态：时光引擎运转中 -->
            <div v-else-if="isProcessing" class="w-full max-w-5xl">
                <!-- 时光引擎专属鎏金主题加载动画 - 参考灵动界面设计 -->
                <div class="relative w-full aspect-video bg-gradient-to-br from-[#0c0a08] to-[#1a1611] backdrop-blur-2xl border border-[#d4af37]/40 rounded-3xl shadow-[0_0_60px_rgba(212,175,55,0.3)] overflow-hidden flex items-center justify-center">
                  
                  <!-- 动态流光背景 -->
                  <div class="absolute inset-0 bg-[conic-gradient(from_0deg,transparent_0%,rgba(212,175,55,0.1)_10%,transparent_20%)] animate-[spin_8s_linear_infinite]"></div>
                  <div class="absolute inset-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_20%,rgba(212,175,55,0.15)_0%,transparent_50%)]"></div>
                  
                  <!-- 扫描线效果 -->
                  <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-[#d4af37] to-transparent shadow-[0_0_20px_4px_rgba(212,175,55,0.7)] scanner-beam"></div>
                  <div class="absolute top-0 left-0 w-full h-32 bg-gradient-to-b from-[#d4af37]/15 to-transparent scanner-trail"></div>
                  
                  <!-- 中央加载内容 -->
                  <div class="relative z-10 text-center space-y-10">
                    <!-- 时光引擎核心图标 -->
                    <div class="relative w-40 h-40 mx-auto">
                      <!-- 外圈光环 -->
                      <div class="absolute inset-0 border-4 border-[#d4af37]/30 rounded-full animate-ping"></div>
                      <!-- 中圈流光 -->
                      <div class="absolute inset-2 border-4 border-[#d4af37]/50 rounded-full animate-spin"></div>
                      <!-- 内圈核心 -->
                      <div class="absolute inset-6 bg-gradient-to-br from-[#d4af37] to-[#f9e0a2] rounded-full shadow-[0_0_40px_rgba(212,175,55,0.8)]">
                        <div class="absolute inset-2 bg-[#1a1611] rounded-full flex items-center justify-center">
                          <FontAwesomeIcon icon="fa-solid fa-hourglass-half" class="text-5xl text-[#d4af37] animate-spin" />
                        </div>
                      </div>
                    </div>
                    
                    <!-- 进度信息 -->
                    <div class="space-y-6">
                      <h3 class="text-4xl font-bold text-[#d4af37] tracking-wider drop-shadow-[0_0_10px_rgba(212,175,55,0.5)]">时光引擎运转中</h3>
                      <p class="text-xl text-[#f9e0a2] font-medium drop-shadow-[0_0_8px_rgba(212,175,55,0.3)]">正在穿越时空修复照片...</p>
                      
                      <!-- 进度条 -->
                      <div class="w-96 mx-auto">
                        <div class="h-4 bg-[#2a241e] rounded-full overflow-hidden shadow-inner border border-[#d4af37]/20">
                          <div 
                            class="h-full bg-gradient-to-r from-[#d4af37] via-[#f5d76e] to-[#f9e0a2] transition-all duration-300 shadow-[0_0_20px_rgba(212,175,55,0.5)]"
                            :style="{ width: timeEngineProgress + '%' }"
                          ></div>
                        </div>
                        <div class="flex justify-between text-sm text-[#8a7f6d] mt-3">
                          <span>0%</span>
                          <span class="text-[#d4af37] font-bold text-lg">{{ Math.round(timeEngineProgress) }}%</span>
                          <span>100%</span>
                        </div>
                      </div>
                      
                      <!-- 处理步骤 -->
                      <div class="grid grid-cols-2 gap-4 max-w-2xl mx-auto">
                        <div class="flex items-center space-x-3 p-3 bg-[#1a1611]/50 rounded-lg border border-[#d4af37]/20">
                          <div class="w-2 h-2 bg-[#d4af37] rounded-full animate-pulse"></div>
                          <span class="text-[#f9e0a2] text-sm">🚀 分析时空特征</span>
                        </div>
                        <div class="flex items-center space-x-3 p-3 bg-[#1a1611]/50 rounded-lg border border-[#d4af37]/20">
                          <div class="w-2 h-2 bg-[#d4af37] rounded-full animate-pulse"></div>
                          <span class="text-[#f9e0a2] text-sm">🎨 生成修复方案</span>
                        </div>
                        <div class="flex items-center space-x-3 p-3 bg-[#1a1611]/50 rounded-lg border border-[#d4af37]/20">
                          <div class="w-2 h-2 bg-[#d4af37] rounded-full animate-pulse"></div>
                          <span class="text-[#f9e0a2] text-sm">✨ 优化色彩细节</span>
                        </div>
                        <div class="flex items-center space-x-3 p-3 bg-[#1a1611]/50 rounded-lg border border-[#d4af37]/20">
                          <div class="w-2 h-2 bg-[#d4af37] rounded-full animate-pulse"></div>
                          <span class="text-[#f9e0a2] text-sm">⏳ 预计600秒</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <!-- 浮动粒子效果 -->
                  <div class="absolute top-6 left-8 w-3 h-3 bg-[#d4af37] rounded-full animate-bounce shadow-[0_0_10px_#d4af37]"></div>
                  <div class="absolute top-12 right-12 w-2 h-2 bg-[#f9e0a2] rounded-full animate-ping shadow-[0_0_8px_#f9e0a2]"></div>
                  <div class="absolute bottom-16 left-1/3 w-2.5 h-2.5 bg-[#d4af37] rounded-full animate-pulse shadow-[0_0_12px_#d4af37]"></div>
                  <div class="absolute bottom-8 right-1/4 w-1.5 h-1.5 bg-[#f5d76e] rounded-full animate-bounce shadow-[0_0_6px_#f5d76e]"></div>
                </div>
                
                <!-- 底部状态提示 -->
                <div class="absolute bottom-8 left-1/2 transform -translate-x-1/2 z-20 flex items-center gap-3 bg-[#1a1611]/80 backdrop-blur-md px-6 py-3 rounded-full border border-[#d4af37]/30 shadow-[0_5px_20px_rgba(212,175,55,0.2)]">
                  <div class="w-2 h-2 rounded-full bg-[#d4af37] shadow-[0_0_8px_#d4af37] animate-ping"></div>
                  <span class="text-[#f9e0a2] text-sm tracking-widest font-medium">ConfUI服务正常，等待AI计算完成...</span>
                </div>
            </div>

            <!-- 3. 结果状态：多图对比展示 -->
            <div v-else-if="resultImage && timeEngineResults.length > 0" class="relative w-full max-w-5xl">
                <div class="text-center mb-6">
                  <h3 class="text-xl font-bold text-gray-800 mb-2">时光引擎修复结果</h3>
                  <p class="text-gray-600">共生成 {{ timeEngineResults.length }} 张修复方案</p>
                </div>
                
                <div class="grid gap-6 mb-6"  
                     :class="timeEngineResults.length === 1 ? 'grid-cols-1 max-w-4xl mx-auto' : 'grid-cols-1 md:grid-cols-2'">
                  
                  <div v-for="(result, index) in timeEngineResults" :key="index" class="bg-white rounded-xl shadow-lg overflow-hidden flex flex-col">
                    <div class="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border-b">
                      <h4 class="font-semibold text-gray-800">方案 {{ index + 1 }}</h4>
                    </div>
                    
                    <div class="relative w-full"  
                         :class="timeEngineResults.length === 1 ? 'h-[500px] md:h-[650px]' : 'h-[350px] md:h-[450px]'">
                      <ImageCompare
                        :beforeImage="selectedPhotoUrl"
                        :afterImage="result"
                        labelBefore="原图"
                        labelAfter="修复后"
                        :enableDownload="true"
                        @download="handleImageDownload"
                        class="w-full h-full"
                      />
                    </div>
                  </div>
                </div>
                
                <div v-if="timeEngineResults.length > 1" class="flex justify-center space-x-4 mb-6">
                  <div 
                    v-for="(result, index) in timeEngineResults" 
                    :key="index"
                    @click="switchTimeEngineResult(index)"
                    class="cursor-pointer border-2 rounded-lg overflow-hidden transition-all duration-300 w-16 h-16"
                    :class="resultImage === result ? 'border-blue-500 scale-110 shadow-md' : 'border-gray-200 hover:border-gray-400 opacity-70'"
                  >
                    <img :src="result" class="w-full h-full object-cover" :alt="'方案' + (index + 1)" />
                  </div>
                </div>
            </div>

            <!-- 4. 预览状态：全息修复台 -->
            <div v-else class="absolute inset-0 flex flex-col items-center justify-center p-8 bg-[#faf8f5] overflow-hidden">
              
              <div class="absolute inset-0 bg-[radial-gradient(circle_at_center,_rgba(212,175,55,0.05)_0%,_transparent_70%)] pointer-events-none animate-pulse-slow"></div>

              <div class="relative z-20 mb-8 flex flex-col items-center">
                <h2 class="text-3xl font-extrabold tracking-[0.3em] liquid-gold-text mb-2 drop-shadow-sm">
                  时光引擎 · 序列重构
                </h2>
                <div class="flex items-center gap-4 opacity-80">
                  <div class="w-16 h-[1px] bg-gradient-to-r from-transparent to-[#d4af37]"></div>
                  <span class="text-[#b8860b] text-[10px] tracking-[0.4em] font-bold uppercase">Flux Node Active</span>
                  <div class="w-16 h-[1px] bg-gradient-to-l from-transparent to-[#d4af37]"></div>
                </div>
              </div>

              <div class="relative z-10 w-full max-w-4xl max-h-[75vh] p-1.5 rounded-2xl overflow-hidden shadow-[0_20px_50px_rgba(212,175,55,0.15)] group">
                
                <div class="absolute top-[-50%] left-[-50%] w-[200%] h-[200%] bg-[conic-gradient(from_0deg,transparent_70%,rgba(212,175,55,0.8)_90%,#f9e0a2_100%)] animate-[spin_4s_linear_infinite] z-0 opacity-80"></div>
                
                <div class="relative z-10 w-full h-full bg-white/85 backdrop-blur-xl rounded-xl p-4 flex items-center justify-center overflow-hidden">
                  
                  <img :src="selectedPhotoUrl" class="max-w-full max-h-[65vh] object-contain relative z-10 rounded-lg shadow-md" />

                  <div class="absolute inset-0 z-20 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-[0.03] mix-blend-overlay pointer-events-none"></div>

                  <div class="absolute inset-0 z-30 pointer-events-none overflow-hidden rounded-lg">
                    <div class="w-full h-[2px] bg-gradient-to-r from-transparent via-[#d4af37] to-transparent shadow-[0_0_20px_4px_rgba(212,175,55,0.7)] scanner-beam"></div>
                    <div class="w-full h-32 bg-gradient-to-b from-[#d4af37]/10 to-transparent scanner-trail"></div>
                  </div>

                </div>
              </div>

              <div class="absolute bottom-8 z-20 flex items-center gap-3 bg-white/60 backdrop-blur-md px-6 py-2 rounded-full border border-white/80 shadow-[0_5px_15px_rgba(212,175,55,0.1)]">
                <div class="w-2 h-2 rounded-full bg-[#d4af37] shadow-[0_0_8px_#d4af37] animate-ping"></div>
                <span class="text-[#8a7f6d] text-xs tracking-widest font-medium">引擎稳定，等待指令注入...</span>
              </div>

            </div>
          </template>

          <!-- ================= 其他模块通用界面 ================= -->
          <template v-else>
            <!-- 1. 空状态：上传 -->
            <div v-if="!selectedPhotoUrl"
                 class="w-full max-w-3xl"
            >
              <!-- 仅流光修复模块显示媒体类型选择 -->
              <div v-if="isColorizeModule" class="mb-8">
                <h3 class="text-lg font-medium text-gray-700 mb-4 text-center">选择媒体类型</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <!-- 图片上传选项 -->
                  <div 
                    class="group relative aspect-video border-2 border-dashed rounded-[2rem] flex flex-col items-center justify-center cursor-pointer transition-all"
                    :class="selectedMediaType === 'image' ? 'border-primary bg-primary/5' : 'border-gray-300 hover:border-primary hover:bg-primary/5'"
                    @click="() => { selectedMediaType = 'image'; triggerUpload() }"
                    @dragover.prevent
                    @drop.prevent="(e) => { selectedMediaType = 'image'; handleDrop(e) }"
                  >
                    <div class="w-20 h-20 bg-white rounded-2xl shadow-sm flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                      <FontAwesomeIcon icon="fa-solid fa-image" class="text-3xl text-gray-400 group-hover:text-primary transition-colors" />
                    </div>
                    <h4 class="text-lg font-medium text-gray-700 group-hover:text-primary transition-colors">上传图片</h4>
                    <p class="text-sm text-gray-400 mt-2">支持 JPG, PNG · 最大 10MB</p>
                  </div>
                  
                  <!-- 视频上传选项 -->
                  <div 
                    class="group relative aspect-video border-2 border-dashed rounded-[2rem] flex flex-col items-center justify-center cursor-pointer transition-all"
                    :class="selectedMediaType === 'video' ? 'border-primary bg-primary/5' : 'border-gray-300 hover:border-primary hover:bg-primary/5'"
                    @click="() => { selectedMediaType = 'video'; triggerUpload() }"
                    @dragover.prevent
                    @drop.prevent="(e) => { selectedMediaType = 'video'; handleDrop(e) }"
                  >
                    <div class="w-20 h-20 bg-white rounded-2xl shadow-sm flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                      <FontAwesomeIcon icon="fa-solid fa-video" class="text-3xl text-gray-400 group-hover:text-primary transition-colors" />
                    </div>
                    <h4 class="text-lg font-medium text-gray-700 group-hover:text-primary transition-colors">上传视频</h4>
                    <p class="text-sm text-gray-400 mt-2">支持 MP4, WebM · 最大 50MB</p>
                  </div>
                </div>
              </div>
              
              <!-- 其他模块显示传统上传区域 -->
              <div v-else
                   class="group relative w-full max-w-2xl aspect-video border-2 border-dashed border-gray-300 rounded-[2rem] flex flex-col items-center justify-center hover:border-primary hover:bg-primary/5 transition-all cursor-pointer"
                   @click="triggerUpload"
                   @dragover.prevent
                   @drop.prevent="handleDrop"
              >
                <div class="w-20 h-20 bg-white rounded-2xl shadow-sm flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                  <FontAwesomeIcon icon="fa-solid fa-cloud-arrow-up" class="text-3xl text-gray-400 group-hover:text-primary transition-colors" />
                </div>
                <h3 class="text-xl font-medium text-gray-700 group-hover:text-primary transition-colors">点击或拖拽上传照片</h3>
                <p class="text-sm text-gray-400 mt-2">支持 JPG, PNG · 最大 10MB</p>
              </div>
              
              <input type="file" ref="fileInput" class="hidden" :accept="selectedMediaType === 'image' ? 'image/*' : 'video/*'" @change="handleFileSelect">
            </div>

          <!-- 2. 预览/结果状态 -->
            <div v-else class="relative w-full h-full flex items-center justify-center p-4">
              <!-- LivePortrait视频显示组件 -->
              <div v-if="moduleId === ModuleStep.LIVE_PORTRAIT" class="w-full h-full">
                <!-- 处理中状态显示LivePortraitVideo组件 -->
                <div v-if="isProcessing">
                  <LivePortraitVideo
                    :videoUrl="resultImage"
                    :isProcessing="isProcessing"
                    :loadingMsg="loadingMsg"
                    :progress="livePortraitProgress"
                    @regenerate="handleLivePortraitProcess"
                    @back="handleLivePortraitBack"
                  />
                </div>
                <!-- 处理完成显示视频 -->
                <div v-else-if="resultImage" class="w-full h-full">
                  <LivePortraitVideo
                    :videoUrl="resultImage"
                    :isProcessing="isProcessing"
                    :loadingMsg="loadingMsg"
                    :progress="livePortraitProgress"
                    @regenerate="handleLivePortraitProcess"
                    @back="handleLivePortraitBack"
                  />
                </div>
                <!-- 处理前显示上传的照片 -->
                <div v-else class="relative w-full h-full flex items-center justify-center">
                  <div class="w-full h-full flex items-center justify-center p-4">
                    <img :src="selectedPhotoUrl" class="w-auto h-auto max-w-[90vw] max-h-[90vh] object-contain shadow-2xl rounded-xl cursor-pointer hover:scale-105 transition-transform duration-300" @click="zoomImage(selectedPhotoUrl, '原图')">
                  </div>
                </div>
              </div>
              
              <!-- 视频预览 -->
              <div v-else-if="isVideo" class="w-full max-w-5xl aspect-video bg-black rounded-xl overflow-hidden shadow-2xl">
                 <video :src="resultImage || selectedPhotoUrl" controls class="w-full h-full object-contain"></video>
              </div>
              
              <!-- 视频预览 -->
              <div v-else-if="isVideo" class="w-full max-w-5xl aspect-video bg-black rounded-xl overflow-hidden shadow-2xl">
                 <video :src="resultImage || selectedPhotoUrl" controls class="w-full h-full object-contain"></video>
              </div>
              
              <!-- 普通图片对比组件 (其他模块结果生成后) -->
              <div v-else-if="resultImage" class="relative w-full max-w-5xl aspect-video">
                <ImageCompare
                  :beforeImage="selectedPhotoUrl"
                  :afterImage="resultImage"
                  labelBefore="修复前"
                  labelAfter="修复后"
                  :enableDownload="true"
                  @download="handleImageDownload"
                  class="w-full h-full rounded-xl shadow-2xl"
                />
              </div>
              
              <!-- 手动涂抹画布 (拂尘手动模式) -->
              <BrushCanvas
                v-else-if="isDustlessModule && repairMode === 'manual'"
                :imageUrl="selectedPhotoUrl"
                @maskChange="handleMaskChange"
                @saveMask="saveMask"
                class="max-h-full shadow-2xl rounded-xl"
              />
              
              <!-- 纯图片预览 (处理前) - 修复照片上传后显示问题 -->
              <div v-else class="relative w-full h-full flex items-center justify-center">
                <div class="w-full h-full flex items-center justify-center p-4">
                  <img :src="selectedPhotoUrl" class="w-auto h-auto max-w-[90vw] max-h-[90vh] object-contain shadow-2xl rounded-xl cursor-pointer hover:scale-105 transition-transform duration-300" @click="zoomImage(selectedPhotoUrl, '原图')">
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- 右侧：控制面板 (Glassy Sidebar) -->
    <div class="w-96 bg-white border-l border-gray-100 flex flex-col shadow-[-10px_0_30px_rgba(0,0,0,0.02)] z-20">
      <!-- 头部信息 -->
      <div class="p-8 pb-4">
        <!-- 动态 Icon 颜色 -->
        <div class="w-12 h-12 rounded-2xl flex items-center justify-center text-xl mb-4"
             :class="isVoiceModule ? 'bg-emerald-50 text-emerald-600' : 'bg-primary/10 text-primary'">
          <component :is="IconWrapper" :icon="moduleConfig.icon" />
        </div>
        <h2 class="font-serif text-2xl font-bold text-gray-900">{{ moduleConfig.name }}</h2>
        <p class="text-sm text-gray-500 mt-2 leading-relaxed">{{ moduleConfig.description }}</p>
      </div>

      <!-- 滚动参数区 -->
      <div class="flex-1 overflow-y-auto px-8 py-4 space-y-8 no-scrollbar">
        
        <!-- === 声音模块参数 === -->
        <VoiceParams 
            v-if="isVoiceModule"
            v-model:params="voiceParams"
        />

        <!-- === 图像模块参数 (有 selectedPhotoUrl 才显示) === -->
        <div v-if="selectedPhotoUrl && !isVoiceModule">
          <!-- 修复模式切换（仅拂尘修复模块显示） -->
          <div v-if="isDustlessModule && !resultImage" class="relative group">
            <button
              @click="toggleRepairMode"
              class="w-full px-5 py-2 rounded-xl font-medium transition-all shadow-md active:scale-95 text-sm flex items-center justify-between"
              :class="repairMode === 'auto' 
                ? 'bg-blue-400 text-white hover:bg-blue-500 shadow-blue-400/30' 
                : repairMode === 'manual' 
                ? 'bg-green-400 text-white hover:bg-green-500 shadow-green-400/30'
                : 'bg-amber-400 text-white hover:bg-amber-500 shadow-amber-400/30'"
            >
              <div class="flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6.75 7.5l3 2.25-3 2.25m4.5 0h3m-9 8.25h13.5A2.25 2.25 0 0 0 21 18V6a2.25 2.25 0 0 0-2.25-2.25H5.25A2.25 2.25 0 0 0 3 6v12a2.25 2.25 0 0 0 2.25 2.25Z" />
                </svg>
                {{ repairMode === 'auto' ? '自动修复' : repairMode === 'manual' ? '手动修复' : '降噪修复' }}
              </div>
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
              </svg>
            </button>
            <div class="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg py-2 opacity-0 group-hover:opacity-100 transition-opacity z-50">
              <div 
                @click="repairMode = 'auto'" 
                class="px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 cursor-pointer flex items-center gap-2"
                :class="repairMode === 'auto' ? 'bg-blue-50 text-blue-600' : ''"
              >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 3v11.25A2.25 2.25 0 0 0 6 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0 1 18 16.5h-2.25m-7.5 0h7.5m-7.5 0-1 3m8.5-3 1 3m0 0 .5 1.5m-.5-1.5h-9.5m0 0-.5 1.5M9 11.25v1.5M12 9v3.75m3-6v6"
                  />
                </svg>
                自动识别修复
              </div>
              <div 
                @click="repairMode = 'manual'" 
                class="px-4 py-2 text-sm text-gray-700 hover:bg-green-50 cursor-pointer flex items-center gap-2"
                :class="repairMode === 'manual' ? 'bg-green-50 text-green-600' : ''"
              >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z"
                  />
                </svg>
                手动涂抹修复
              </div>
              <div 
                @click="repairMode = 'denoise'" 
                class="px-4 py-2 text-sm text-gray-700 hover:bg-amber-50 cursor-pointer flex items-center gap-2"
                :class="repairMode === 'denoise' ? 'bg-amber-50 text-amber-600' : ''"
              >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 0 1-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 0 1 4.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0 1 12 15a9.065 9.065 0 0 0-6.23-.693L5 14.5m14.8.8 1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0 1 12 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5"
                  />
                </svg>
                降噪修复
              </div>
            </div>
          </div>
        
        <!-- 动态加载参数组件 -->
        <!-- 拂尘修复参数 -->
        <DustlessParams
          v-if="isDustlessModule"
          v-model:params="dustlessParams"
          v-model:repair-mode="repairMode"
        />
        
        <!-- 流光修复参数 -->
        <LiuguangParams
          v-if="isColorizeModule"
          v-model:params="colorizeParams"
          ref="liuguangParamsRef"
        />
        
        <!-- 清影修复参数 -->
        <QingyingParams
          v-if="isQingyingModule"
          v-model:params="qingyingParams"
          @recognize-text="handleTextRecognition"
        />
        
        <!-- 真容修复参数 -->
        <ZhenrongParams
          v-if="moduleId === ModuleStep.ZHENRONG"
          v-model:params="zhenrongParams"
        />

        <!-- 灵动·人像复活参数 -->
        <LivePortraitParams
          v-if="moduleId === ModuleStep.LIVE_PORTRAIT"
          v-model:params="livePortraitParams"
        />

        <!-- 时光引擎参数 -->
        <TimeEngineParams
          v-if="isTimeEngineModule"
        />

        <!-- 记忆注脚 (声音模块不显示) -->
        <div class="pt-6 border-t border-dashed border-gray-200">
          <label class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-2">
            <i class="fa-regular fa-pen-to-square"></i> 记忆注脚
          </label>
          <textarea
            class="w-full p-4 bg-gray-50 border-0 rounded-2xl text-sm focus:ring-2 focus:ring-primary/20 focus:bg-white transition resize-none h-32 placeholder-gray-400"
            placeholder="写下这张照片背后的故事..."
          ></textarea>
        </div>
        </div>
      </div>

      <!-- 底部操作区 -->
      <div class="p-8 pt-4 bg-white border-t border-gray-50">
        
        <!-- 声音模块按钮 -->
        <button 
           v-if="isVoiceModule"
           @click="handleVoiceProcess"
           :disabled="isProcessing || !voiceParams.text"
           class="w-full py-4 rounded-xl font-bold text-white shadow-xl transition-all transform hover:-translate-y-1 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed bg-gradient-to-r from-emerald-600 to-teal-600 shadow-emerald-500/20"
        >
          {{ isProcessing ? '正在合成...' : '开始合成声音' }}
        </button>

        <!-- 图像模块按钮 -->
        <div v-else-if="selectedPhotoUrl">
            <!-- 修复完成后 -->
            <div v-if="resultImage" class="flex flex-col gap-4">
              <button
                @click="continueRepair"
                :disabled="isProcessing"
                class="w-full py-4 rounded-xl font-bold text-white bg-primary-400 hover:bg-primary-500 shadow-xl shadow-primary-400/10 transition-all transform hover:-translate-y-1 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                继续修复
              </button>
              
              <button
                v-if="isColorizeModule"
                @click="enhanceColor"
                :disabled="isProcessing"
                class="w-full py-4 rounded-xl font-bold text-white bg-indigo-600 hover:bg-indigo-700 shadow-xl shadow-indigo-600/10 transition-all transform hover:-translate-y-1 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <FontAwesomeIcon icon="fa-solid fa-palette" class="mr-2" /> 增强色彩
              </button>
              
              <button
                v-if="isColorizeModule && originalResultImage"
                @click="undoColorEnhance"
                :disabled="isProcessing"
                class="w-full py-4 rounded-xl font-bold text-white bg-amber-600 hover:bg-amber-700 shadow-xl shadow-amber-600/10 transition-all transform hover:-translate-y-1 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <FontAwesomeIcon icon="fa-solid fa-rotate-left" class="mr-2" /> 回退色彩增强
              </button>
            </div>
            
            <!-- 未完成修复 -->
            <button v-else
                @click="handleProcess"
                :disabled="isProcessing"
                class="w-full py-4 rounded-xl font-bold text-white bg-gray-900 hover:bg-black shadow-xl shadow-gray-900/10 transition-all transform hover:-translate-y-1 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {{ isLivePortraitModule ? '开始生成人像动画' : repairMode === 'auto' ? '开始智能修复' : repairMode === 'manual' ? '开始手动修复' : '开始降噪修复' }}
            </button>
        </div>
        
         <div v-else class="text-center text-sm text-gray-400 py-2">
            请先上传照片
         </div>
      </div>
    </div>
  </div>
  <div v-else>Module Not Found</div>
</template>

<style scoped>
.animate-fade-in {
    animation: fadeIn 0.5s ease-out;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* ================= 时光引擎专属时空穿梭特效 ================= */

/* --- 时空之门穿越特效 (白金风格) --- */
.stargate-container {
  perspective: 1000px; /* 创造3D空间深度 */
  background: radial-gradient(circle at center, #ffffff 0%, #faf8f5 100%);
}

.stargate-tunnel {
  position: absolute;
  top: 50%; left: 50%;
  width: 0; height: 0;
  transform-style: preserve-3d;
}

/* 隧道光环 */
.stargate-ring {
  position: absolute;
  top: -300px; left: -300px;
  width: 600px; height: 600px;
  border: 2px solid rgba(212, 175, 55, 0.4); /* 金色光环 */
  border-radius: 50%;
  box-shadow: 
    0 0 40px rgba(212, 175, 55, 0.2), 
    inset 0 0 40px rgba(212, 175, 55, 0.2);
  /* 穿越动画：从小变大，从远及近 */
  animation: warp-drive 6s linear infinite;
  opacity: 0;
}

/* 错开每个光环的出现时间，形成连绵不断的隧道感 */
.stargate-ring:nth-child(1) { animation-delay: 0s; }
.stargate-ring:nth-child(2) { animation-delay: -1.5s; }
.stargate-ring:nth-child(3) { animation-delay: -3s; }
.stargate-ring:nth-child(4) { animation-delay: -4.5s; }

@keyframes warp-drive {
  0% {
    transform: translateZ(-800px) scale(0.1);
    opacity: 0;
  }
  30% {
    opacity: 1;
  }
  100% {
    /* 光环冲出屏幕，变大并消失 */
    transform: translateZ(600px) scale(2.5);
    opacity: 0;
  }
}

/* 核心悬浮球交互发光 */
 .core-hover:hover {
   box-shadow: 0 0 80px rgba(212, 175, 55, 0.5), inset 0 0 30px rgba(255, 255, 255, 0.8);
 }

 /* --- 1. 液态流金文字特效 (Liquid Gold) --- */
 .liquid-gold-text {
   background: linear-gradient(
     -45deg, 
     #b8860b 20%, 
     #fceabb 40%, 
     #d4af37 60%, 
     #b8860b 80%
   );
   background-size: 200% auto;
   color: transparent;
   -webkit-background-clip: text;
   background-clip: text;
   animation: liquid-flow 4s linear infinite;
 }

 @keyframes liquid-flow {
   0% { background-position: 200% center; }
   100% { background-position: 0% center; }
 }

 /* --- 2. 扫描线光束 (Scanner Beam) --- */
 .scanner-beam {
   position: absolute;
   top: 0;
   animation: scan-move 3s cubic-bezier(0.4, 0, 0.2, 1) infinite alternate;
 }

 /* 扫描线拖尾 */
 .scanner-trail {
   position: absolute;
   top: 0;
   transform: translateY(-100%); /* 紧跟光束上方 */
   animation: scan-move 3s cubic-bezier(0.4, 0, 0.2, 1) infinite alternate;
 }

 @keyframes scan-move {
   0% { top: 0%; opacity: 0; }
   10% { opacity: 1; }
   90% { opacity: 1; }
   100% { top: 100%; opacity: 0; }
 }

 /* --- 3. 背景缓慢呼吸脉冲 --- */
 .animate-pulse-slow {
   animation: slow-pulse 6s ease-in-out infinite alternate;
 }

 @keyframes slow-pulse {
   0% { opacity: 0.5; transform: scale(0.95); }
   100% { opacity: 1; transform: scale(1.05); }
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

/* 时光引擎金色高亮样式 */
.time-engine-highlight {
    background: linear-gradient(135deg, #d4af37 0%, #f5d76e 50%, #d4af37 100%);
    background-size: 200% 200%;
    animation: golden-glow 3s ease-in-out infinite;
    box-shadow: 0 0 30px rgba(212, 175, 55, 0.4);
    border: 2px solid rgba(212, 175, 55, 0.3);
}

@keyframes golden-glow {
    0%, 100% { 
        background-position: 0% 50%; 
        box-shadow: 0 0 30px rgba(212, 175, 55, 0.4);
    }
    50% { 
        background-position: 100% 50%; 
        box-shadow: 0 0 50px rgba(212, 175, 55, 0.7);
    }
}

.time-engine-pulse {
    animation: golden-pulse 2s ease-in-out infinite;
}

@keyframes golden-pulse {
    0%, 100% { 
        transform: scale(1);
        box-shadow: 0 0 20px rgba(212, 175, 55, 0.3);
    }
    50% { 
        transform: scale(1.05);
        box-shadow: 0 0 40px rgba(212, 175, 55, 0.6);
    }
}

.custom-audio {
    height: 48px;
    border-radius: 24px;
    background-color: #f0fdf4; /* emerald-50 */
}
/* Webkit 浏览器音频控件样式微调 */
.custom-audio::-webkit-media-controls-panel {
    background-color: #f0fdf4;
}
.custom-audio::-webkit-media-controls-play-button,
.custom-audio::-webkit-media-controls-mute-button {
    background-color: #d1fae5; /* emerald-100 */
    border-radius: 50%;
}
</style>
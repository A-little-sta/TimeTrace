import { ModuleConfig, ModuleStep } from './types';
import { h } from 'vue';

// 根据生产/开发环境自动切换
// import.meta.env.VITE_API_BASE 是 Vite 的环境变量写法
export const API_BASE_URL = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api/v1';

// 静态文件服务地址
export const STATIC_BASE_URL = import.meta.env.VITE_STATIC_BASE || 'http://localhost:8000';

// 轮播图数据 - 使用五个模块的对比图
export const SLIDES = [
  {
    id: 1,
    title: '拂尘 · 物理修复',
    desc: '智能去除照片中的划痕、污渍和瑕疵，恢复照片原始洁净。',
    before: '/images/dustless_before.png',
    after: '/images/dustless_after.jpg'
  },
  {
    id: 2,
    title: '拂尘 · 去噪修复',
    desc: '基于UHDM超高清降噪算法，智能去除摩尔纹和图像噪声，让照片恢复纯净清晰。',
    before: '/images/denoise_before.jpg',
    after: '/images/denoise_after.jpg'
  },
  {
    id: 3,
    title: '流光 · 色彩复苏',
    desc: '为黑白照片注入自然色彩，重现那个年代的鲜活记忆。',
    before: '/images/colorize_before.jpg',
    after: '/images/colorize_after.jpg'
  },
  {
    id: 4,
    title: '清影 · 画质重构',
    desc: '智能提升照片清晰度，让模糊的细节变得锐利清晰。',
    before: '/images/qingying_before.png',
    after: '/images/qingying_after.jpg'
  },
  {
    id: 5,
    title: '真容 · 肖像精修',
    desc: '专业修复人物面部细节，找回亲人最清晰真实的模样。',
    before: '/images/zhenrong_before.png',
    after: '/images/zhenrong_after.jpg'
  }
];

// We define icons as functional components or SVG strings for Vue
// For simplicity in this structure, we return VNodes directly using 'h'
// In a real project, these might be separate .vue files

const DustlessIcon = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", strokeWidth: 1.2, stroke: "currentColor", class: "w-6 h-6" }, [
    h('path', { strokeLinecap: "round", strokeLinejoin: "round", d: "M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 0 0-2.456 2.456ZM16.894 20.567 16.5 21.75l-.394-1.183a2.25 2.25 0 0 0-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 0 0 1.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 0 0 1.423 1.423l1.183.394-1.183.394a2.25 2.25 0 0 0-1.423 1.423Z" })
]);

const LiuguangIcon = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", strokeWidth: 1.2, stroke: "currentColor", class: "w-6 h-6" }, [
    h('path', { strokeLinecap: "round", strokeLinejoin: "round", d: "M12 3v2.25m6.364.386-1.591 1.591M21 12h-2.25m-.386 6.364-1.591-1.591M12 18.75V21m-4.773-4.227-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0Z" })
]);

const QingyingIcon = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", strokeWidth: 1.2, stroke: "currentColor", class: "w-6 h-6" }, [
    h('path', { strokeLinecap: "round", strokeLinejoin: "round", d: "M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z" }),
    h('path', { strokeLinecap: "round", strokeLinejoin: "round", d: "M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" })
]);

const ZhenrongIcon = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", strokeWidth: 1.2, stroke: "currentColor", class: "w-6 h-6" }, [
    h('path', { strokeLinecap: "round", strokeLinejoin: "round", d: "M15.182 15.182a4.5 4.5 0 0 1-6.364 0M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0ZM9.75 9.75c0 .414-.168.75-.375.75S9 10.164 9 9.75 9.168 9 9.375 9s.375.336.375.75Zm-.375 0h.008v.015h-.008V9.75Zm5.625 0c0 .414-.168.75-.375.75s-.375-.336-.375-.75.168-.75.375-.75.375.336.375.75Zm-.375 0h.008v.015h-.008V9.75Z" })
]);

const EchoIcon = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", strokeWidth: 1.2, stroke: "currentColor", class: "w-6 h-6" }, [
    h('path', { strokeLinecap: "round", strokeLinejoin: "round", d: "M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" }),
    h('path', { strokeLinecap: "round", strokeLinejoin: "round", d: "M15.91 11.672a.375.375 0 0 1 0 .656l-5.603 3.113a.375.375 0 0 1-.557-.328V8.887c0-.286.307-.466.557-.327l5.603 3.112Z" })
]);

const VoiceIcon = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", strokeWidth: 1.2, stroke: "currentColor", class: "w-6 h-6" }, [
    h('path', { strokeLinecap: "round", strokeLinejoin: "round", d: "M12 18.75a6 6 0 0 0 6-6v-1.5m-6 7.5a6 6 0 0 1-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 0 1-3-3V4.5a3 3 0 1 1 6 0v8.25a3 3 0 0 1-3 3Z" })
]);

const LivePortraitIcon = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", strokeWidth: 1.2, stroke: "currentColor", class: "w-6 h-6" }, [
    h('path', { strokeLinecap: "round", strokeLinejoin: "round", d: "M15.75 10.5l4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z" })
]);

const TimeEngineIcon = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", strokeWidth: 1.2, stroke: "currentColor", class: "w-6 h-6" }, [
    h('path', { strokeLinecap: "round", strokeLinejoin: "round", d: "M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" }),
    h('path', { strokeLinecap: "round", strokeLinejoin: "round", d: "M12 2.25c-5.385 0-9.75 4.365-9.75 9.75s4.365 9.75 9.75 9.75 9.75-4.365 9.75-9.75S17.385 2.25 12 2.25Zm0 18c-4.962 0-9-4.038-9-9s4.038-9 9-9 9 4.038 9 9-4.038 9-9 9Z" })
]);

const DimensionSculptorIcon = h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", strokeWidth: 1.2, stroke: "currentColor", class: "w-6 h-6" }, [
    h('path', { strokeLinecap: "round", strokeLinejoin: "round", d: "M21 7.5l-9-5.25L3 7.5m18 0l-9 5.25m9-5.25v9l-9 5.25M3 7.5l9 5.25M3 7.5v9l9 5.25m0-9v9" })
]);

export const MODULES: ModuleConfig[] = [
  {  
    id: ModuleStep.DUSTLESS,
    name: '拂尘修复',
    description: '拂去岁月尘埃，重现往日洁净。',
    color: 'bg-stone-100 text-stone-600',
    icon: DustlessIcon,
    iconBg: 'bg-stone-100',
    iconColor: 'text-stone-600',
    iconName: 'fa-solid magic',
    emotionalTexts: [
      '正在拂去岁月尘埃...',
      '小心修补每一道裂痕...',
      '让老照片重获新生...'
    ],
    technicalTexts: [
      '识别纸张折痕与污渍',
      '智能生成缺失像素',
      '无缝融合修复区域'
    ]
  },
  {
    id: ModuleStep.LIUGUANG,
    name: '流光修复',
    description: '点亮记忆光影，赋予画面新生。',
    color: 'bg-amber-100 text-amber-700',
    icon: LiuguangIcon,
    iconBg: 'bg-amber-100',
    iconColor: 'text-amber-700',
    iconName: 'fa-solid fa-palette',
    emotionalTexts: [
      '为照片注入生命色彩...',
      '重现那个年代的温度...',
      '让黑白记忆活起来...'
    ],
    technicalTexts: [
      '分析场景色彩上下文',
      '预测合理颜色分布',
      '优化色彩过渡自然度'
    ]
  },
  {
    id: ModuleStep.QINGYING,
    name: '清影修复',
    description: '重塑清晰轮廓，找回失落细节。',
    color: 'bg-sky-100 text-sky-700',
    icon: QingyingIcon,
    iconBg: 'bg-sky-100',
    iconColor: 'text-sky-700',
    iconName: 'fa-solid fa-mountain-sun',
    emotionalTexts: [
      '正在重塑画面细节...',
      '让模糊变得锐利清晰...',
      '还原每一个精彩瞬间...'
    ],
    technicalTexts: [
      '生成式模型重绘',
      '智能填充细节信息',
      '提升图像分辨率'
    ]
  },
  {
    id: ModuleStep.ZHENRONG,
    name: '真容修复',
    description: '精修面部神态，还原至亲容颜。',
    color: 'bg-rose-100 text-rose-700',
    icon: ZhenrongIcon,
    iconBg: 'bg-rose-100',
    iconColor: 'text-rose-700',
    iconName: 'fa-regular fa-face-smile',
    emotionalTexts: [
      '正在勾勒面部轮廓...',
      '让亲人的笑容更清晰...',
      '穿越时空的凝视...'
    ],
    technicalTexts: [
      '人脸关键点检测',
      '面部几何重建',
      '五官细节增强'
    ]
  },
  {
    id: ModuleStep.VOICE,
    name: '留音',
    description: '让记忆中的声音穿越时空，再次在耳边响起。',
    color: 'bg-emerald-100 text-emerald-700',
    icon: VoiceIcon,
    iconBg: 'bg-emerald-100',
    iconColor: 'text-emerald-700',
    iconName: 'fa-solid fa-microphone-lines',
    emotionalTexts: [
      '正在合成自然语音...',
      '让记忆中的声音重现...',
      '跨越时空的声音对话...'
    ],
    technicalTexts: [
      'TTS语音合成处理',
      '声纹特征提取',
      '音频质量优化'
    ]
  },
  {
    id: ModuleStep.LIVE_PORTRAIT,
    name: '灵动 · 人像复活',
    description: '音频驱动人像说话，让照片中的人物开口说话。',
    color: 'bg-indigo-100 text-indigo-700',
    icon: LivePortraitIcon,
    iconBg: 'bg-indigo-100',
    iconColor: 'text-indigo-700',
    iconName: 'fa-solid fa-video',
    emotionalTexts: [
      '正在让照片开口说话...',
      '让人物表情栩栩如生...',
      '跨越时空的对话...'
    ],
    technicalTexts: [
      '音频驱动面部动画',
      '表情同步技术',
      '视频合成处理'
    ]
  },
  {
    id: ModuleStep.TIME_ENGINE,
    name: '时光引擎',
    description: '基于Flux.1 Pro的AI一键修复，让老照片重获新生。',
    color: 'bg-gradient-to-r from-[#d4af37] to-[#f5d76e] text-white',
    icon: TimeEngineIcon,
    iconBg: 'bg-gradient-to-r from-[#d4af37] to-[#f5d76e]',
    iconColor: 'text-white',
    iconName: 'fa-solid fa-bolt',
    isCore: true,
    emotionalTexts: [
      '时光引擎启动中...',
      'Flux模型正在重塑画面...',
      '让岁月痕迹焕发新生...'
    ],
    technicalTexts: [
      'Flux.1 Pro超强模型',
      'ComfyUI节点工作流',
      '智能多维度修复'
    ]
  },
  {
    id: ModuleStep.DIMENSION_SCULPTOR,
    name: '维度重塑',
    description: '2D照片转3D模型，上传照片一键生成可交互的立体影像。',
    color: 'bg-amber-100 text-amber-700',
    icon: DimensionSculptorIcon,
    iconBg: 'bg-amber-100',
    iconColor: 'text-amber-700',
    iconName: 'fa-solid fa-cube',
    emotionalTexts: [
      '正在从照片重建立体世界...',
      'AI正在推算空间结构...',
      '让平面影像跃然而出...'
    ],
    technicalTexts: [
      'Tripo3D深度学习引擎',
      '单帧图像3D重建',
      'PBR物理渲染材质'
    ]
  },
];

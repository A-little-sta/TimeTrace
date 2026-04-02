export interface Photo {
  id: number; 
  filename: string;
  original_path: string;
  user_id?: number;
  created_at?: string;
  url?: string; 
}

export interface Task {
  id: number;
  task_type: 'single' | 'combined';
  steps: string[];
  current_step: number;
  photo_id: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  result_path?: string;
  step_results?: string[];
  error_message?: string;
  progress?: number;
  created_at: string;
  updated_at?: string;
  completed_at?: string;
}

export enum ModuleStep {
  DUSTLESS = 'dustless',
  LIUGUANG = 'liuguang',
  QINGYING = 'qingying',
  ZHENRONG = 'zhenrong',
  VOICE = 'voice',
  LIVE_PORTRAIT = 'live_portrait',
  TIME_ENGINE = 'time_engine',
}

export interface ModuleConfig {
  id: ModuleStep;
  name: string;
  description: string;
  icon: any; // Vue VNode or component
  color: string;
  isComingSoon?: boolean;
  isCore?: boolean;
}

export interface History {
  id: number;
  user_id: number;
  task_id?: number;
  media_type: string; // image, audio
  operation_type: string; // dustless, colorize, clarity, trueface, tts, voice_clone
  input_path: string; // 输入文件路径（原图或原音频）
  result_path: string;
  params?: Record<string, any>;
  created_at: string;
  updated_at?: string;
  input_url?: string;
  result_url?: string;
}
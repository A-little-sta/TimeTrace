import { API_BASE_URL, STATIC_BASE_URL } from '../constants';
import { Photo, Task, History } from '../types';
import axios from 'axios';

// Helper to construct full image URLs
export const getFullImageUrl = (path: string | undefined): string => {
  if (!path) return '';
  if (path.startsWith('http')) return path;
  
  // 处理 Windows 的反斜杠问题，统一转为正斜杠
  let cleanPath = path.replace(/\\/g, '/');
  
  // Remove any leading slashes
  cleanPath = cleanPath.startsWith('/') ? cleanPath.substring(1) : cleanPath;
  
  // 关键修复：后端返回的路径已经是static/uploads/...格式
  // 我们只需要确保没有重复的static前缀，然后直接拼接
  
  // Remove duplicate static prefixes
  while (cleanPath.startsWith('static/static/')) {
    cleanPath = cleanPath.replace('static/static/', 'static/');
  }
  
  // 如果路径已经以static/开头，直接使用
  // 如果路径不以static/开头，说明是相对路径，需要添加static/
  if (!cleanPath.startsWith('static/')) {
    cleanPath = `static/${cleanPath}`;
  }
  
  // Add timestamp to prevent browser caching
  const timestamp = new Date().getTime();
  
  // 关键修复：直接拼接，不需要再添加static/
  // STATIC_BASE_URL已经是http://localhost:8000，路径是static/uploads/...
  // 拼接后就是http://localhost:8000/static/uploads/...
  return `${STATIC_BASE_URL}/${cleanPath}?t=${timestamp}`;
};

// 创建 axios 实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // AI 处理可能慢，设置较长超时
});

class ApiService {
  private getAuthHeaders() {
    const token = localStorage.getItem('token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
  }

  // --- Auth --- 

  async register(username: string, email: string, password: string) {
    const response = await apiClient.post('/auth/register', {
      username,
      email,
      password
    });
    return response.data;
  }

  async login(username: string, password: string) {
    const response = await apiClient.post('/auth/login', 
      new URLSearchParams({ username, password }),
      { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
    );
    return response.data;
  }

  async getCurrentUser(token: string) {
    const response = await apiClient.get('/auth/me', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    return response.data;
  }

  // --- Gallery --- 

  async uploadPhoto(file: File): Promise<Photo> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post('/gallery/photos/upload', formData, {
      headers: {
        ...this.getAuthHeaders(),
        // 不要设置Content-Type，让浏览器自动处理multipart/form-data
      }
    });

    const photo = response.data;
    // Add full URL for frontend usage
    return {
        ...photo,
        url: getFullImageUrl(photo.original_path)
    };
  }

  async getPhotos(skip = 0, limit = 100): Promise<Photo[]> {
    const response = await apiClient.get('/gallery/photos', {
      params: { skip, limit },
      headers: {
        ...this.getAuthHeaders()
      }
    });
    const photos: Photo[] = response.data;
    
    return photos.map(p => ({
        ...p,
        url: getFullImageUrl(p.original_path)
    }));
  }

  async deletePhoto(photoId: number): Promise<void> {
    await apiClient.delete(`/gallery/photos/${photoId}`, {
      headers: {
        ...this.getAuthHeaders()
      }
    });
  }

  async deleteAllPhotos(): Promise<void> {
    await apiClient.delete('/gallery/photos/delete-all', {
      headers: {
        ...this.getAuthHeaders()
      }
    });
  }

  // --- Workshop --- 

  /**
   * 创建修复任务（直接上传图片）
   * @param moduleType 模块代码 (如 'dustless', 'zhenrong')
   * @param file 图片文件对象 (必须是 File 类型)
   * @param prompt (可选) 提示词
   * @param params (可选) 模块参数
   * @param maskId (可选) 掩码ID
   * @param usePowerPaint (可选) 是否使用PowerPaint模型
   * @param taskType (可选) PowerPaint任务类型
   * @param repairMode (可选) 修复模式 (auto:自动修复, manual:手动修复, denoise:降噪修复)
   */
  async createTask(moduleType: string, file: File, prompt?: string, params?: Record<string, any>, maskId?: number, usePowerPaint: boolean = true, taskType: string = 'object-removal', repairMode: string = 'auto'): Promise<Task> {
    // 1. 构造 FormData 对象 (这是后端接收 UploadFile 的唯一方式)
    const formData = new FormData();
    
    // 2. 添加关键字段
    // 后端定义: module: str = Form(...)
    formData.append('module', moduleType);
    
    // 后端定义: file: UploadFile = File(...)
    formData.append('file', file);
    
    // 后端定义: prompt: str = Form(None)
    if (prompt) {
      formData.append('prompt', prompt);
    }
    
    // 添加PowerPaint相关参数
    formData.append('use_powerpaint', usePowerPaint.toString());
    formData.append('task_type', taskType);
    
    // 添加修复模式参数
    formData.append('repair_mode', repairMode);
    
    // 添加模块参数
    if (params) {
      formData.append('params', JSON.stringify(params));
    }
    
    // 添加掩码ID（如果有）
    if (maskId) {
      formData.append('mask_id', maskId.toString());
    }

    console.log(`🚀 [API] 发送任务: Module=${moduleType}, File=${file.name}, Size=${file.size}`);

    try {
      // 3. 发送请求
      const response = await apiClient.post('/workshop/tasks', formData, {
        headers: {
          ...this.getAuthHeaders(),
          // 不要设置Content-Type，让浏览器自动处理multipart/form-data
        },
      });
      return response.data;
    } catch (error) {
      console.error("❌ [API] 创建任务失败:", error);
      throw error;
    }
  }

  /**
   * 创建修复任务（从图库选择图片）
   * @param photoId 图片ID
   * @param moduleType 模块代码
   * @param params (可选) 模块参数
   * @param maskId (可选) 掩码ID
   * @param usePowerPaint (可选) 是否使用PowerPaint模型
   * @param taskType (可选) PowerPaint任务类型
   * @param repairMode (可选) 修复模式
   */
  async createTaskFromGallery(photoId: number, moduleType: string, params?: Record<string, any>, maskId?: number, usePowerPaint: boolean = true, taskType: string = 'object-removal', repairMode: string = 'auto'): Promise<Task> {
    console.log(`🚀 [API] 从图库创建任务: PhotoID=${photoId}, Module=${moduleType}`);

    try {
      // 发送JSON请求
      const requestData: any = {
        photo_id: photoId,
        steps: [moduleType],
        task_type: 'single',
        use_powerpaint: usePowerPaint,
        powerpaint_task_type: taskType,
        repair_mode: repairMode
      };
      
      // 添加模块参数
      if (params) {
        requestData.params = params;
      }
      
      // 添加掩码ID（如果有）
      if (maskId) {
        requestData.mask_id = maskId;
      }
      
      const response = await apiClient.post('/workshop/tasks', requestData, {
        headers: {
          ...this.getAuthHeaders(),
          'Content-Type': 'application/json'
        },
      });
      return response.data;
    } catch (error) {
      console.error("❌ [API] 从图库创建任务失败:", error);
      throw error;
    }
  }

  /**
   * 识别图像中的文字
   * @param photoId 图片ID
   */
  async recognizeText(photoId: number): Promise<{ text: string }> {
    console.log(`🚀 [API] 识别图片文字: PhotoID=${photoId}`);
    
    try {
      const response = await apiClient.post('/workshop/recognize-text', {
        photo_id: photoId
      }, {
        headers: {
          ...this.getAuthHeaders(),
          'Content-Type': 'application/json'
        },
      });
      return response.data;
    } catch (error) {
      console.error("❌ [API] 文字识别失败:", error);
      throw error;
    }
  }

  /**
   * 获取用户的修复历史记录
   * @param skip 跳过的记录数
   * @param limit 获取的记录数
   */
  async getHistories(skip = 0, limit = 20): Promise<History[]> {
    console.log(`🚀 [API] 获取历史记录: Skip=${skip}, Limit=${limit}`);
    
    try {
      const response = await apiClient.get('/workshop/histories', {
        params: { skip, limit },
        headers: {
          ...this.getAuthHeaders()
        }
      });
      const histories: History[] = response.data;
      
      // 为每条历史记录添加完整的URL
      return histories.map(history => ({
        ...history,
        input_url: getFullImageUrl(history.input_path),
        result_url: getFullImageUrl(history.result_path)
      }));
      
    } catch (error) {
      console.error("❌ [API] 获取历史记录失败:", error);
      throw error;
    }
  }

  /**
   * 获取正在处理中的任务
   */
  async getActiveTasks(): Promise<Task[]> {
    console.log(`🚀 [API] 获取正在处理中的任务`);
    
    try {
      const response = await apiClient.get('/workshop/tasks/active', {
        headers: {
          ...this.getAuthHeaders()
        }
      });
      const tasks: Task[] = response.data;
      
      console.log(`✅ [API] 获取到 ${tasks.length} 个正在处理的任务`);
      return tasks;
      
    } catch (error) {
      console.error("❌ [API] 获取正在处理中的任务失败:", error);
      throw error;
    }
  }

  /**
   * 获取任务详情
   * @param taskId 任务ID
   */
  async getTask(taskId: number): Promise<Task> {
    console.log(`🚀 [API] 获取任务详情: ID=${taskId}`);
    
    try {
      const response = await apiClient.get(`/workshop/tasks/${taskId}`, {
        headers: {
          ...this.getAuthHeaders()
        }
      });
      const task: Task = response.data;
      
      console.log(`✅ [API] 任务详情获取成功: ID=${taskId}, Status=${task.status}`);
      return task;
      
    } catch (error) {
      console.error("❌ [API] 获取任务详情失败:", error);
      throw error;
    }
  }

  /**
   * 删除历史记录
   * @param historyId 历史记录ID
   */
  async deleteHistory(historyId: number): Promise<void> {
    console.log(`🗑️ [API] 删除历史记录: ID=${historyId}`);
    
    try {
      await apiClient.delete(`/workshop/histories/${historyId}`, {
        headers: {
          ...this.getAuthHeaders()
        }
      });
      console.log("✅ [API] 历史记录删除成功");
    } catch (error) {
      console.error("❌ [API] 删除历史记录失败:", error);
      throw error;
    }
  }

  /**
   * 清空所有历史记录
   */
  async clearAllHistories(): Promise<{message: string}> {
    console.log("🗑️ [API] 清空所有历史记录");
    
    try {
      const response = await apiClient.delete('/workshop/histories', {
        headers: {
          ...this.getAuthHeaders()
        }
      });
      console.log("✅ [API] 清空历史记录成功");
      return response.data;
    } catch (error) {
      console.error("❌ [API] 清空历史记录失败:", error);
      throw error;
    }
  }
}

export const api = new ApiService();
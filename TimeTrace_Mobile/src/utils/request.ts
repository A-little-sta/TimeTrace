/**
 * 岁月笺影 - 移动端网络请求封装
 * 基于 uni.request，统一处理 BaseURL、Token 注入、全局错误响应
 */

// 后端 API 基础地址
const BASE_URL = 'http://localhost:8000/api/v1'

// Token 在本地存储中的 key
const TOKEN_KEY = 'token'

// 用户信息在本地存储中的 key
const USER_KEY = 'user_info'

/**
 * 获取本地存储的 Token
 */
export function getToken(): string {
  return uni.getStorageSync(TOKEN_KEY) || ''
}

/**
 * 设置 Token 到本地存储
 */
export function setToken(token: string): void {
  uni.setStorageSync(TOKEN_KEY, token)
}

/**
 * 移除 Token
 */
export function removeToken(): void {
  uni.removeStorageSync(TOKEN_KEY)
}

/**
 * 获取本地存储的用户信息
 */
export function getUserInfo() {
  const data = uni.getStorageSync(USER_KEY)
  return data ? JSON.parse(data) : null
}

/**
 * 设置用户信息到本地存储
 */
export function setUserInfo(user: any): void {
  uni.setStorageSync(USER_KEY, JSON.stringify(user))
}

/**
 * 移除用户信息
 */
export function removeUserInfo(): void {
  uni.removeStorageSync(USER_KEY)
}

/**
 * 通用请求方法
 * @param options 请求配置
 */
function request<T = any>(options: {
  url: string
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  data?: any
  header?: Record<string, string>
  contentType?: string
}): Promise<T> {
  return new Promise((resolve, reject) => {
    const token = getToken()
    const header: Record<string, string> = {
      ...options.header,
    }

    // 注入 Token
    if (token) {
      header['Authorization'] = `Bearer ${token}`
    }

    // 设置 Content-Type（默认 JSON）
    if (options.contentType === 'form') {
      header['Content-Type'] = 'application/x-www-form-urlencoded'
    } else if (!header['Content-Type']) {
      header['Content-Type'] = 'application/json'
    }

    uni.request({
      url: `${BASE_URL}${options.url}`,
      method: options.method || 'GET',
      data: options.data,
      header,
      success: (res) => {
        const statusCode = res.statusCode

        // 401 未授权 - 跳转登录页
        if (statusCode === 401) {
          removeToken()
          removeUserInfo()
          uni.showToast({ title: '登录已过期，请重新登录', icon: 'none' })
          setTimeout(() => {
            uni.reLaunch({ url: '/pages/login/login' })
          }, 1500)
          reject(new Error('登录已过期'))
          return
        }

        // 500 服务器异常
        if (statusCode >= 500) {
          uni.showToast({ title: '服务器开小差了，请稍后再试', icon: 'none' })
          reject(new Error('服务器异常'))
          return
        }

        // 422 参数校验错误
        if (statusCode === 422) {
          const detail = (res.data as any)?.detail
          const msg = Array.isArray(detail)
            ? detail.map((d: any) => d.msg).join('; ')
            : '输入数据格式不正确'
          reject(new Error(msg))
          return
        }

        // 400 业务错误
        if (statusCode === 400) {
          const detail = (res.data as any)?.detail || '请求参数有误'
          reject(new Error(detail))
          return
        }

        // 其他非 2xx 状态码
        if (statusCode < 200 || statusCode >= 300) {
          const detail = (res.data as any)?.detail || '请求失败'
          reject(new Error(detail))
          return
        }

        // 成功
        resolve(res.data as T)
      },
      fail: (err) => {
        uni.showToast({ title: '网络连接失败，请检查网络', icon: 'none' })
        reject(new Error('网络连接失败'))
      },
    })
  })
}

/**
 * GET 请求
 */
export function get<T = any>(url: string, data?: any): Promise<T> {
  return request<T>({ url, method: 'GET', data })
}

/**
 * POST 请求（JSON 格式）
 */
export function post<T = any>(url: string, data?: any): Promise<T> {
  return request<T>({ url, method: 'POST', data })
}

/**
 * POST 请求（application/x-www-form-urlencoded 格式）
 * 后端 OAuth2PasswordRequestForm 要求此格式
 */
export function postForm<T = any>(url: string, data: Record<string, string>): Promise<T> {
  // 将对象转为 URL 编码字符串
  const formBody = Object.keys(data)
    .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(data[key])}`)
    .join('&')
  return request<T>({ url, method: 'POST', data: formBody, contentType: 'form' })
}

/**
 * PUT 请求
 */
export function put<T = any>(url: string, data?: any): Promise<T> {
  return request<T>({ url, method: 'PUT', data })
}

/**
 * DELETE 请求
 */
export function del<T = any>(url: string, data?: any): Promise<T> {
  return request<T>({ url, method: 'DELETE', data })
}

/**
 * 文件上传（uni.uploadFile 封装）
 */
export function uploadFile<T = any>(options: {
  url: string
  filePath: string
  name?: string
  formData?: Record<string, any>
}): Promise<T> {
  return new Promise((resolve, reject) => {
    const token = getToken()
    const header: Record<string, string> = {}
    if (token) {
      header['Authorization'] = `Bearer ${token}`
    }

    uni.uploadFile({
      url: `${BASE_URL}${options.url}`,
      filePath: options.filePath,
      name: options.name || 'file',
      formData: options.formData,
      header,
      success: (res) => {
        const statusCode = res.statusCode
        if (statusCode === 401) {
          removeToken()
          removeUserInfo()
          uni.showToast({ title: '登录已过期，请重新登录', icon: 'none' })
          setTimeout(() => {
            uni.reLaunch({ url: '/pages/login/login' })
          }, 1500)
          reject(new Error('登录已过期'))
          return
        }
        if (statusCode >= 500) {
          uni.showToast({ title: '服务器开小差了，请稍后再试', icon: 'none' })
          reject(new Error('服务器异常'))
          return
        }
        if (statusCode < 200 || statusCode >= 300) {
          try {
            const data = JSON.parse(res.data)
            reject(new Error(data.detail || '上传失败'))
          } catch {
            reject(new Error('上传失败'))
          }
          return
        }
        try {
          const data = JSON.parse(res.data)
          resolve(data as T)
        } catch {
          reject(new Error('响应解析失败'))
        }
      },
      fail: () => {
        uni.showToast({ title: '网络连接失败，请检查网络', icon: 'none' })
        reject(new Error('网络连接失败'))
      },
    })
  })
}

export default request

// ============================================================
// 语音生成专用请求（处理二进制音频响应）
// 对应后端 POST /workshop/voice/generate
// 后端返回 Response(content=wav_bytes, media_type="audio/wav")
// responseType:arraybuffer + 全局 try-catch 兜底，Promise 永不挂起
// ============================================================

/**
 * 语音生成请求
 * - TTS 模式(无文件)：uni.request + responseType:arraybuffer → 写文件 / base64 降级
 * - 克隆模式(有文件)：uni.uploadFile 上传参考音频
 * @returns 临时音频文件路径 或 base64 data URL
 */
export function voiceGenerate(params: {
  text: string
  mode: 'tts' | 'clone'
  voiceId?: string
  rate?: string
  promptText?: string
  refAudioPath?: string
}): Promise<string> {
  const token = getToken()
  const rate = params.rate || '+0%'
  const REQUEST_TIMEOUT = 120000

  if (params.mode === 'tts') {
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        reject(new Error('语音生成请求超时，请检查网络或服务状态'))
      }, REQUEST_TIMEOUT)

      const formBody = [
        `text=${encodeURIComponent(params.text)}`,
        `mode=tts`,
        `rate=${encodeURIComponent(rate)}`,
        `voice_id=${encodeURIComponent(params.voiceId || 'female1')}`,
      ].join('&')

      uni.request({
        url: `${BASE_URL}/workshop/voice/generate`,
        method: 'POST',
        data: formBody,
        header: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'Authorization': token ? `Bearer ${token}` : '',
        },
        responseType: 'arraybuffer',
        success: (res: any) => {
          try {
            clearTimeout(timer)
            if (res.statusCode !== 200) {
              let errMsg = '语音生成失败'
              try {
                const dec = new TextDecoder()
                const json = JSON.parse(dec.decode(res.data))
                errMsg = json.detail || json.message || errMsg
              } catch { /* use default */ }
              reject(new Error(errMsg))
              return
            }
            const rawData: any = res.data
            if (!rawData) { reject(new Error('生成的音频数据为空')); return }

            let buffer: ArrayBuffer
            if (rawData instanceof ArrayBuffer) {
              buffer = rawData
            } else if (typeof rawData === 'string') {
              const bytes = new Uint8Array(rawData.length)
              for (let i = 0; i < rawData.length; i++) bytes[i] = rawData.charCodeAt(i) & 0xFF
              buffer = bytes.buffer
            } else if (rawData.buffer instanceof ArrayBuffer) {
              buffer = rawData.buffer
            } else {
              reject(new Error('音频数据格式异常'))
              return
            }
            if (buffer.byteLength === 0) { reject(new Error('生成的音频数据为空')); return }

            // 尝试写临时文件（App 原生端），失败则降级 base64 data URL（H5 端）
            const toBase64 = (buf: ArrayBuffer) => {
              const bytes = new Uint8Array(buf)
              let binary = ''
              for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i])
              return `data:audio/wav;base64,${btoa(binary)}`
            }
            try {
              const fs = uni.getFileSystemManager()
              const tempPath = `${uni.env.USER_DATA_PATH}/voice_${Date.now()}.wav`
              fs.writeFile({
                filePath: tempPath,
                data: buffer,
                success: () => resolve(tempPath),
                fail: () => resolve(toBase64(buffer)),
              })
            } catch {
              resolve(toBase64(buffer))
            }
          } catch (err: any) {
            clearTimeout(timer)
            reject(new Error(err.message || '音频处理异常'))
          }
        },
        fail: (err: any) => {
          clearTimeout(timer)
          reject(new Error('网络请求失败: ' + (err.errMsg || '请检查网络连接')))
        },
      })
    })
  }

  // 克隆模式：需要上传参考音频文件
  return new Promise((resolve, reject) => {
    if (!params.refAudioPath) {
      reject(new Error('声音克隆需要参考音频文件'))
      return
    }

    const timer = setTimeout(() => {
      reject(new Error('声音克隆请求超时，请检查服务状态'))
    }, REQUEST_TIMEOUT)

    uni.uploadFile({
      url: `${BASE_URL}/workshop/voice/generate`,
      filePath: params.refAudioPath,
      name: 'ref_audio',
      formData: {
        text: params.text,
        mode: 'clone',
        rate,
        prompt_text: params.promptText || '',
      },
      header: {
        'Authorization': token ? `Bearer ${token}` : '',
      },
      success: (res) => {
        try {
          clearTimeout(timer)
          if (res.statusCode !== 200) {
            let errMsg = '声音克隆失败'
            try { const json = JSON.parse(res.data); errMsg = json.detail || errMsg } catch { /* use default */ }
            reject(new Error(errMsg))
            return
          }
          const fs = uni.getFileSystemManager()
          const tempPath = `${uni.env.USER_DATA_PATH}/voice_${Date.now()}.wav`
          const bytes = new Uint8Array(res.data.length)
          for (let i = 0; i < res.data.length; i++) bytes[i] = res.data.charCodeAt(i) & 0xFF
          const toBase64 = () => {
            let binary = ''
            for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i])
            return `data:audio/wav;base64,${btoa(binary)}`
          }
          fs.writeFile({
            filePath: tempPath,
            data: bytes.buffer,
            success: () => resolve(tempPath),
            fail: () => resolve(toBase64()),
          })
        } catch (err: any) {
          clearTimeout(timer)
          reject(new Error(err.message || '音频处理异常'))
        }
      },
      fail: (err: any) => {
        clearTimeout(timer)
        reject(new Error('网络请求失败: ' + (err.errMsg || '请检查网络连接')))
      },
    })
  })
}

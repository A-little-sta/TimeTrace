import { defineStore } from 'pinia';
import { ref } from 'vue';
import router from './router';
import { api } from './services/api';

export const useAuthStore = defineStore('auth', () => {
  const user = ref<{ id: number; username: string; email: string } | null>(null);
  const isAuthenticated = ref(false);

  // Initialize from local storage if needed
  const token = localStorage.getItem('token');
  if (token) {
    // 尝试从后端获取用户信息
    (async () => {
      try {
        const userData = await api.getCurrentUser(token);
        user.value = userData;
        isAuthenticated.value = true;
      } catch (error) {
        // 如果获取用户信息失败，清除本地存储
        localStorage.removeItem('token');
        user.value = null;
        isAuthenticated.value = false;
      }
    })();
  }

  async function login(username: string, password: string) {
    // 调用真实的API
    try {
      const response = await api.login(username, password);
      if (response.access_token) {
        // 保存token到本地存储
        localStorage.setItem('token', response.access_token);
        // 设置用户信息
        user.value = response.user;
        isAuthenticated.value = true;
      }
    } catch (error) {
      // 登录失败，抛出错误
      throw error;
    }
  }

  async function register(username: string, email: string, password: string) {
    // 调用真实的API
    try {
      await api.register(username, email, password);
      // 注册成功后自动登录
      await login(username, password);
    } catch (error) {
      // 注册失败，抛出错误
      throw error;
    }
  }

  function logout() {
    // 清除本地存储和状态
    localStorage.removeItem('token');
    user.value = null;
    isAuthenticated.value = false;
    router.push('/login');
  }

  return { user, isAuthenticated, login, register, logout };
});
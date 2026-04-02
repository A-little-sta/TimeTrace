<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../store';

const username = ref('');
const password = ref('');
const isLoading = ref(false);
const errorMessage = ref('');
const router = useRouter();
const authStore = useAuthStore();

const handleLogin = async () => {
  if (!username.value || !password.value) {
    errorMessage.value = '请输入用户名和密码';
    return;
  }
  
  isLoading.value = true;
  errorMessage.value = '';
  
  try {
    await authStore.login(username.value, password.value);
    router.push('/app');
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '登录失败，请检查用户名和密码';
  } finally {
    isLoading.value = false;
  }
};
</script>

<template>
  <div class="min-h-screen flex bg-white font-sans text-gray-900 selection:bg-primary-100 selection:text-primary-700">
    <div class="hidden lg:flex flex-1 relative overflow-hidden group bg-gray-100">
      <img 
        src="../assets/images/login.jpg"
        alt="Vintage Photo Album" 
        class="absolute inset-0 w-full h-full object-cover transition-transform duration-[20s] ease-linear scale-100 group-hover:scale-105"
      />
      
      <div class="absolute inset-0 bg-gradient-to-t from-gray-900/90 via-gray-900/30 to-transparent z-10"></div>
      
      <div class="relative z-20 flex flex-col justify-end p-16 w-full">
        <div class="backdrop-blur-md bg-white/5 border border-white/10 p-8 rounded-3xl shadow-2xl shadow-black/5 overflow-hidden relative">
            <div class="absolute top-0 left-0 w-full h-full bg-gradient-to-br from-white/10 to-transparent pointer-events-none"></div>
            
            <div class="mb-6 w-16 h-1.5 bg-primary-400 rounded-full shadow-[0_0_10px_rgba(96,165,250,0.5)]"></div>
            <h1 class="text-5xl font-serif font-bold leading-tight mb-4 tracking-wide text-white drop-shadow-sm">
              重拾<span class="text-primary-300 italic">岁月</span>的温度
            </h1>
            <p class="text-lg text-gray-200 font-light leading-relaxed max-w-lg">
              TimeTrace 利用先进 AI 技术，修复、上色并复活您的珍贵老照片。让记忆不再斑驳，让爱意跨越时间。
            </p>
        </div>
      </div>
    </div>

    <div class="flex-1 flex flex-col items-center justify-center p-8 sm:p-24 relative bg-white">
      <div class="w-full max-w-[420px] space-y-10 animate-slide-up">
        
        <div class="text-center space-y-4">
            <div class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary-50 text-primary-600 mb-2 shadow-sm ring-1 ring-primary-100 transition-transform duration-500 hover:rotate-6">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.8" stroke="currentColor" class="w-8 h-8">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z" />
                </svg>
            </div>
            <div>
                <h2 class="text-3xl font-bold text-gray-900 tracking-tight">欢迎回来</h2>
                <p class="mt-2 text-gray-500 text-[15px]">登录以访问您的时光图库</p>
            </div>
        </div>

        <form class="space-y-6" @submit.prevent="handleLogin">
          <div class="space-y-5">
            <div class="group relative">
              <label for="username" class="block text-sm font-semibold text-gray-700 mb-1.5 ml-1">用户名</label>
              <div class="relative transition-all duration-300 transform focus-within:-translate-y-0.5">
                  <input 
                    id="username" 
                    v-model="username"
                    type="text" 
                    required 
                    class="peer w-full px-5 py-4 bg-gray-50 border-0 text-gray-900 rounded-2xl focus:bg-white focus:ring-2 focus:ring-primary-500/20 focus:shadow-lg focus:shadow-primary-500/10 transition-all placeholder-gray-400 font-medium" 
                    placeholder="请输入您的用户名" 
                  />
                  <div class="absolute bottom-0 left-2 right-2 h-0.5 bg-primary-500 scale-x-0 transition-transform duration-300 peer-focus:scale-x-100 origin-center opacity-50"></div>
              </div>
            </div>
            
            <div class="group relative">
              <label for="password" class="block text-sm font-semibold text-gray-700 mb-1.5 ml-1">密码</label>
              <div class="relative transition-all duration-300 transform focus-within:-translate-y-0.5">
                  <input 
                    id="password" 
                    v-model="password"
                    type="password" 
                    required 
                    class="peer w-full px-5 py-4 bg-gray-50 border-0 text-gray-900 rounded-2xl focus:bg-white focus:ring-2 focus:ring-primary-500/20 focus:shadow-lg focus:shadow-primary-500/10 transition-all placeholder-gray-400 font-medium" 
                    placeholder="••••••••" 
                  />
                   <div class="absolute bottom-0 left-2 right-2 h-0.5 bg-primary-500 scale-x-0 transition-transform duration-300 peer-focus:scale-x-100 origin-center opacity-50"></div>
              </div>
            </div>
          </div>

          <div class="flex items-center justify-between text-sm pt-1 px-1">
            <label class="flex items-center group cursor-pointer select-none">
              <div class="relative">
                  <input id="remember-me" type="checkbox" class="peer sr-only" />
                  <div class="w-5 h-5 border-2 border-gray-300 rounded-md peer-checked:bg-primary-600 peer-checked:border-primary-600 transition-all"></div>
                  <svg class="absolute top-0.5 left-0.5 w-4 h-4 text-white opacity-0 peer-checked:opacity-100 transition-opacity" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M20 6L9 17l-5-5" stroke-linecap="round" stroke-linejoin="round"/></svg>
              </div>
              <span class="ml-2.5 text-gray-600 font-medium group-hover:text-gray-900 transition-colors">记住我</span>
            </label>
            <a href="#" class="font-semibold text-primary-600 hover:text-primary-500 transition-colors hover:underline decoration-2 underline-offset-4">忘记密码?</a>
          </div>

          <div v-if="errorMessage" class="p-4 rounded-xl bg-red-50 border border-red-100 text-red-600 text-sm font-medium flex items-center gap-3 animate-shake">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" /></svg>
            {{ errorMessage }}
          </div>

          <button 
            type="submit" 
            :disabled="isLoading"
            class="group relative w-full flex justify-center py-4 px-4 border border-transparent text-[16px] font-bold rounded-2xl text-white bg-gray-900 hover:bg-gray-800 transition-all shadow-[0_4px_10px_rgba(0,0,0,0.15)] hover:shadow-[0_8px_20px_rgba(0,0,0,0.2)] hover:-translate-y-0.5 active:translate-y-0 active:scale-[0.98] disabled:opacity-70 disabled:cursor-not-allowed overflow-hidden"
          >
            <div class="absolute inset-0 -translate-x-full group-hover:animate-shimmer bg-gradient-to-r from-transparent via-white/10 to-transparent z-10"></div>
            
            <span v-if="!isLoading" class="relative z-20">登 录</span>
            <span v-else class="flex items-center relative z-20">
                <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                正在验证...
            </span>
          </button>
        </form>

        <p class="text-center text-[15px] text-gray-500">
           还没有账号? 
           <a @click="$router.push('/register')" class="font-bold text-primary-600 hover:text-primary-500 cursor-pointer transition-colors ml-1 px-2 py-1 rounded-lg hover:bg-primary-50">立即注册</a>
        </p>
      </div>
      
      <div class="absolute bottom-8 text-xs text-gray-400 tracking-wider font-medium">
        © 2026 Lihaha Labs.
      </div>
    </div>
  </div>
</template>

<style scoped>
.animate-slide-up {
  animation: slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards; /* More natural easing */
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.animate-shake {
  animation: shake 0.5s cubic-bezier(.36,.07,.19,.97) both;
}

@keyframes shake {
  10%, 90% { transform: translate3d(-1px, 0, 0); }
  20%, 80% { transform: translate3d(2px, 0, 0); }
  30%, 50%, 70% { transform: translate3d(-4px, 0, 0); }
  40%, 60% { transform: translate3d(4px, 0, 0); }
}

@keyframes shimmer {
  100% { transform: translateX(100%); }
}
.group-hover\:animate-shimmer {
  animation: shimmer 1.5s infinite;
}
</style>
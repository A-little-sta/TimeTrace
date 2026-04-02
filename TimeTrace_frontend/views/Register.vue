<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../store';

const username = ref('');
const email = ref('');
const password = ref('');
const isLoading = ref(false);
const errorMessage = ref('');
const router = useRouter();
const authStore = useAuthStore();

const handleRegister = async () => {
  if (!username.value || !email.value || !password.value) {
    errorMessage.value = '请填写完整的注册信息';
    return;
  }
  
  isLoading.value = true;
  errorMessage.value = '';
  
  try {
    await authStore.register(username.value, email.value, password.value);
    router.push('/');
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '注册失败，请稍后重试';
  } finally {
    isLoading.value = false;
  }
};
</script>

<template>
  <div class="min-h-screen flex bg-white font-sans text-gray-900 selection:bg-primary-100 selection:text-primary-700">
    <div class="hidden lg:flex flex-1 relative overflow-hidden group bg-stone-100">
       <img 
         src="https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?q=80&w=2748&auto=format&fit=crop" 
         alt="Vintage Camera" 
         class="absolute inset-0 w-full h-full object-cover mix-blend-multiply opacity-80 transition-transform duration-[25s] ease-in-out scale-100 group-hover:scale-110"
       />
       <div class="absolute inset-0 bg-gradient-to-t from-stone-900/80 via-transparent to-transparent z-10"></div>
       
       <div class="relative z-20 flex flex-col justify-end p-16 w-full h-full text-white">
         <div class="backdrop-blur-md bg-stone-900/30 border border-white/10 p-10 rounded-3xl shadow-2xl relative overflow-hidden transform transition-all duration-700 hover:bg-stone-900/40">
             <div class="mt-auto pl-4 border-l-4 border-primary-400">
                 <h1 class="text-5xl font-serif font-bold leading-none mb-6 drop-shadow-lg">
                   注册<br/>
                   <span class="text-3xl font-light text-primary-200 block mt-4 tracking-wider">开启时光之旅</span>
                 </h1>
                 <p class="text-lg text-gray-100 font-light max-w-md leading-relaxed">加入 TimeTrace 社区，AI 将为您拂去岁月的尘埃，还原记忆的色彩。</p>
             </div>
         </div>
       </div>
    </div>

    <div class="flex-1 flex flex-col items-center justify-center p-8 sm:p-24 relative bg-white">
      <div class="w-full max-w-[420px] space-y-10 animate-slide-up">
        
        <div class="text-center space-y-3">
            <h2 class="text-3xl font-bold text-gray-900 tracking-tight">创建新账户</h2>
            <p class="text-gray-500 text-[15px]">仅需几秒钟，即可开始使用</p>
        </div>

        <form class="space-y-5" @submit.prevent="handleRegister">
          <div class="group relative">
             <label for="username" class="block text-sm font-semibold text-gray-700 mb-1.5 ml-1">用户名</label>
             <div class="relative">
               <svg class="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5 transition-colors duration-300 group-focus-within:text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                 <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
               </svg>
               <input 
                 id="username" 
                 v-model="username"
                 type="text" 
                 required 
                 class="w-full pl-12 pr-4 py-4 bg-gray-50 border-transparent text-gray-900 rounded-2xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:shadow-lg focus:shadow-primary-500/10 transition-all placeholder-gray-400 font-medium" 
                 placeholder="设置一个好记的名字" 
               />
             </div>
          </div>

          <div class="group relative">
             <label for="email" class="block text-sm font-semibold text-gray-700 mb-1.5 ml-1">邮箱</label>
             <div class="relative">
               <svg class="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5 transition-colors duration-300 group-focus-within:text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                 <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
               </svg>
               <input 
                 id="email" 
                 v-model="email"
                 type="email" 
                 required 
                 class="w-full pl-12 pr-4 py-4 bg-gray-50 border-transparent text-gray-900 rounded-2xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:shadow-lg focus:shadow-primary-500/10 transition-all placeholder-gray-400 font-medium" 
                 placeholder="example@email.com" 
               />
             </div>
          </div>

          <div class="group relative">
             <label for="password" class="block text-sm font-semibold text-gray-700 mb-1.5 ml-1">密码</label>
             <div class="relative">
               <svg class="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5 transition-colors duration-300 group-focus-within:text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                 <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
               </svg>
               <input 
                 id="password" 
                 v-model="password"
                 type="password" 
                 required 
                 class="w-full pl-12 pr-4 py-4 bg-gray-50 border-transparent text-gray-900 rounded-2xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:shadow-lg focus:shadow-primary-500/10 transition-all placeholder-gray-400 font-medium" 
                 placeholder="至少6位字符" 
               />
             </div>
          </div>

          <div v-if="errorMessage" class="p-4 rounded-xl bg-red-50 border border-red-100 text-red-600 text-sm font-medium text-center animate-shake">
            {{ errorMessage }}
          </div>

          <button 
            type="submit" 
            :disabled="isLoading"
            class="group relative w-full flex justify-center py-4 px-4 border border-transparent text-[16px] font-bold rounded-2xl text-white bg-gray-900 hover:bg-gray-800 transition-all shadow-[0_4px_10px_rgba(0,0,0,0.1)] hover:shadow-[0_8px_20px_rgba(0,0,0,0.2)] hover:-translate-y-0.5 active:translate-y-0 active:scale-[0.98] disabled:opacity-70 disabled:cursor-not-allowed overflow-hidden"
          >
            <div class="absolute inset-0 -translate-x-full group-hover:animate-shimmer bg-gradient-to-r from-transparent via-white/10 to-transparent z-10"></div>
            <span v-if="!isLoading" class="relative z-20">创建一个账户</span>
            <span v-else class="flex items-center relative z-20">
              <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              注册中...
            </span>
          </button>
        </form>

        <p class="text-center text-[15px] text-gray-500">
           已有账号? 
           <a @click="$router.push('/login')" class="font-bold text-primary-600 hover:text-primary-500 cursor-pointer transition-colors ml-1 px-2 py-1 rounded-lg hover:bg-primary-50">直接登录</a>
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
  animation: slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
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
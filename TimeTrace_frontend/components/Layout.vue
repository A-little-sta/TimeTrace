<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { MODULES } from '../constants';
import { useAuthStore } from '../store';
import NotificationCenter from './NotificationCenter.vue';

const notificationCenter = ref<InstanceType<typeof NotificationCenter>>();

const route = useRoute();
const router = useRouter(); // needed for navigation
const authStore = useAuthStore();

const sidebarOpen = ref(false);
const sidebarHidden = ref(false);

const toggleSidebar = () => {
  sidebarOpen.value = !sidebarOpen.value;
};

const closeSidebar = () => {
  sidebarOpen.value = false;
};

// 处理侧边栏隐藏事件（来自 History.vue 的图片详情）
const handleSidebarHide = (event: CustomEvent) => {
  sidebarHidden.value = event.detail.hide;
};

const isActive = (path: string) => {
  if (path === '/') return route.path === '/';
  return route.path.startsWith(path);
};

// 检查模块是否开放（所有模块都已开放）
const isModuleOpen = (moduleId: string) => {
  // 所有模块都已开放
  return true;
};

const navigateTo = (path: string) => {
    // 使用replace代替push，避免在模块间切换时污染路由历史记录
    if (path.startsWith('/workshop/')) {
        router.replace(path);
    } else {
        router.push(path);
    }
};

// 处理模块点击
const handleModuleClick = (moduleId: string) => {
  if (isModuleOpen(moduleId)) {
    navigateTo(`/workshop/${moduleId}`);
  } else {
    // 显示未开放提示
    const moduleName = MODULES.find(m => m.id === moduleId)?.name || '该功能';
    alert(`${moduleName}功能正在开发中，敬请期待！`);
    // 仍然允许导航到页面，但显示提示
    navigateTo(`/workshop/${moduleId}`);
  }
};

const handleLogout = () => {
    authStore.logout();
    router.push('/login');
};

// 处理通知事件
const handleNotification = (event: CustomEvent) => {
  if (notificationCenter.value) {
    // 调用通知组件的添加通知方法
    notificationCenter.value.addNotification(event.detail);
  }
};

onMounted(() => {
  // 监听通知事件
  window.addEventListener('time_trace_notification', handleNotification);
  // 监听侧边栏隐藏事件
  window.addEventListener('time_trace_hide_sidebar', handleSidebarHide);
});

onUnmounted(() => {
  // 移除事件监听器
  window.removeEventListener('time_trace_notification', handleNotification);
  // 移除侧边栏隐藏事件监听器
  window.removeEventListener('time_trace_hide_sidebar', handleSidebarHide);
});
</script>

<template>
  <div class="flex h-screen w-full bg-background text-gray-800 font-sans overflow-hidden">
    <!-- 手机端遮罩层 -->
    <div 
      v-if="sidebarOpen" 
      class="fixed inset-0 bg-black/50 z-30 lg:hidden transition-opacity duration-300"
      @click="closeSidebar"
    ></div>

    <!-- 手机端顶部导航栏 -->
    <div class="lg:hidden fixed top-0 left-0 right-0 h-14 bg-white/90 backdrop-blur-md border-b border-primary-100/50 z-20 flex items-center px-4 shadow-sm">
      <button @click="toggleSidebar" class="w-10 h-10 flex items-center justify-center rounded-xl hover:bg-gray-100 transition">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6 text-gray-700">
          <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
        </svg>
      </button>
      <div class="flex items-center gap-2 ml-3">
        <div class="w-7 h-7 rounded-full bg-primary-400 flex items-center justify-center text-white shadow-sm">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
          </svg>
        </div>
        <h1 class="text-lg font-serif-title font-bold tracking-tight text-gray-900">岁月笺影</h1>
      </div>
    </div>

    <!-- Sidebar -->
    <aside 
      :class="[
        'fixed lg:static inset-y-0 left-0 w-72 bg-white/80 backdrop-blur-md border-r border-primary-100/50 flex flex-col flex-shrink-0 z-40 lg:z-20 shadow-[4px_0_30px_rgba(207,176,123,0.1)] transition-all duration-300 ease-in-out overflow-y-auto',
        sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
        sidebarHidden ? 'pointer-events-none' : ''
      ]"
    >
      <div class="p-8 pb-4">
        <div class="flex items-center justify-between mb-10">
          <div class="flex flex-col gap-1">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-primary-400 flex items-center justify-center text-white shadow-lg shadow-primary-400/40">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
                </svg>
              </div>
              <h1 class="text-2xl font-serif-title font-bold tracking-tight text-gray-900">岁月笺影</h1>
            </div>
            <p class="text-xs text-primary-600/80 font-medium tracking-widest pl-14 uppercase">TimeTrace</p>
          </div>
          <button @click="closeSidebar" class="lg:hidden w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-100 transition">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5 text-gray-500">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Navigation Links -->
        <div class="space-y-2">
            <!-- Dashboard Link -->
            <div 
                @click="navigateTo('/')"
                :class="[
                    'flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 group relative overflow-hidden cursor-pointer',
                    isActive('/') ? 'bg-gradient-to-r from-primary-400/20 to-primary-400/5 text-primary-800 font-medium shadow-sm' : 'text-gray-500 hover:bg-gray-100 hover:text-gray-900'
                ]"
            >
                <span :class="['transition-transform duration-300', isActive('/') ? 'scale-110 text-primary-600' : 'group-hover:scale-110']">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 3v11.25A2.25 2.25 0 0 0 6 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0 1 18 16.5h-2.25m-7.5 0h7.5m-7.5 0-1 3m8.5-3 1 3m0 0 .5 1.5m-.5-1.5h-9.5m0 0-.5 1.5M9 11.25v1.5M12 9v3.75m3-6v6" />
                    </svg>
                </span>
                <span class="font-sans text-sm tracking-wide z-10">修复工坊</span>
                <div v-if="isActive('/')" class="absolute left-0 top-0 bottom-0 w-1 bg-primary-400 rounded-r-full"></div>
            </div>
            
            <!-- Gallery Link -->
            <div 
                @click="navigateTo('/gallery')"
                :class="[
                    'flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 group relative overflow-hidden cursor-pointer',
                    isActive('/gallery') ? 'bg-gradient-to-r from-primary-400/20 to-primary-400/5 text-primary-800 font-medium shadow-sm' : 'text-gray-500 hover:bg-gray-100 hover:text-gray-900'
                ]"
            >
                <span :class="['transition-transform duration-300', isActive('/gallery') ? 'scale-110 text-primary-600' : 'group-hover:scale-110']">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
                        <path stroke-linecap="round" stroke-linejoin="round" d="m2.25 15.75 5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 0 0 1.5-1.5V6a1.5 1.5 0 0 0-1.5-1.5H3.75A1.5 1.5 0 0 0 2.25 6v12a1.5 1.5 0 0 0 1.5 1.5Zm10.5-11.25h.008v.008h-.008V8.25Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z" />
                    </svg>
                </span>
                <span class="font-sans text-sm tracking-wide z-10">时光图库</span>
                <div v-if="isActive('/gallery')" class="absolute left-0 top-0 bottom-0 w-1 bg-primary-400 rounded-r-full"></div>
            </div>
            
            <!-- History Link -->
            <div 
                @click="navigateTo('/history')"
                :class="[
                    'flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 group relative overflow-hidden cursor-pointer',
                    isActive('/history') ? 'bg-gradient-to-r from-primary-400/20 to-primary-400/5 text-primary-800 font-medium shadow-sm' : 'text-gray-500 hover:bg-gray-100 hover:text-gray-900'
                ]"
            >
                <span :class="['transition-transform duration-300', isActive('/history') ? 'scale-110 text-primary-600' : 'group-hover:scale-110']">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
                    </svg>
                </span>
                <span class="font-sans text-sm tracking-wide z-10">创作时光轴</span>
                <div v-if="isActive('/history')" class="absolute left-0 top-0 bottom-0 w-1 bg-primary-400 rounded-r-full"></div>
            </div>
            
            <!-- Help Center Link -->
            <div 
                @click="navigateTo('/help-center')"
                :class="[
                    'flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 group relative overflow-hidden cursor-pointer',
                    isActive('/help-center') ? 'bg-gradient-to-r from-primary-400/20 to-primary-400/5 text-primary-800 font-medium shadow-sm' : 'text-gray-500 hover:bg-gray-100 hover:text-gray-900'
                ]"
            >
                <span :class="['transition-transform duration-300', isActive('/help-center') ? 'scale-110 text-primary-600' : 'group-hover:scale-110']">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 5.25h.008v.008H12v-.008Z" />
                    </svg>
                </span>
                <span class="font-sans text-sm tracking-wide z-10">使用指南</span>
                <div v-if="isActive('/help-center')" class="absolute left-0 top-0 bottom-0 w-1 bg-primary-400 rounded-r-full"></div>
            </div>
        </div>

        <div class="mt-10 mb-4 flex items-center gap-2 px-4">
          <div class="h-px bg-primary-200 flex-1"></div>
          <span class="text-[10px] font-bold text-primary-400 uppercase tracking-widest">修复工坊</span>
          <div class="h-px bg-primary-200 flex-1"></div>
        </div>

        <!-- Modules List -->
        <div class="space-y-2">
          <template v-for="module in MODULES" :key="module.id">
            <div 
                @click="handleModuleClick(module.id)"
                :class="[
                    'flex items-center gap-3 rounded-xl transition-all duration-300 group relative overflow-hidden cursor-pointer',
                    module.isCore ? 'nav-item-time-engine mt-4 mb-2' : 'px-4 py-3',
                    isActive(`/workshop/${module.id}`) && !module.isCore ? 'bg-gradient-to-r from-primary-400/20 to-primary-400/5 text-primary-800 font-medium shadow-sm' : 
                    isModuleOpen(module.id) ? 'text-gray-500 hover:bg-gray-100 hover:text-gray-900' : 'text-gray-400 hover:bg-gray-50'
                ]"
            >
                <span :class="['transition-transform duration-300 flex items-center justify-center w-5 h-5', 
                    isActive(`/workshop/${module.id}`) ? 'scale-110 text-primary-600' : 
                    isModuleOpen(module.id) ? 'group-hover:scale-110' : 'scale-90 grayscale group-hover:scale-100']">
                     <component :is="module.icon" />
                </span>
                <span class="font-sans text-sm tracking-wide z-10">{{ module.name.split(' ')[0] }}</span>
                <div v-if="isActive(`/workshop/${module.id}`) && !module.isCore" class="absolute left-0 top-0 bottom-0 w-1 bg-primary-400 rounded-r-full"></div>
            </div>
          </template>
        </div>
      </div>

      <div class="mt-auto p-6 border-t border-primary-50 space-y-3">
        <!-- 消息通知 -->
        <NotificationCenter ref="notificationCenter" />
        
        <!-- 用户登出 -->
        <button @click="handleLogout" class="flex items-center gap-3 px-4 py-3 w-full text-sm text-gray-600 hover:bg-primary-50 hover:text-primary-700 rounded-xl transition-all duration-300 group">
          <div class="w-9 h-9 rounded-full bg-gray-100 group-hover:bg-primary-200 group-hover:text-primary-800 flex items-center justify-center transition-colors">
            <span class="font-serif-title font-bold text-xs">我</span>
          </div>
          <div class="flex flex-col items-start">
            <span class="font-medium">用户</span>
            <span class="text-xs text-gray-400 group-hover:text-primary-500">登出</span>
          </div>
        </button>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 overflow-y-auto relative bg-background scroll-smooth pt-14 lg:pt-0">
      <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-primary-300 to-transparent opacity-50 z-10 pointer-events-none"></div>
      <router-view></router-view>
    </main>
  </div>
</template>

<style scoped>
/* 专属时光引擎菜单的流光外框 - 白金毛玻璃质感 */
.nav-item-time-engine {
  position: relative;
  background-color: transparent;
  padding: 14px 16px;
  cursor: pointer;
  color: #b8860b !important; /* 深金棕色，更易阅读 */
  font-weight: bold;
  letter-spacing: 0.1em;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(212, 175, 55, 0.15);
  /* 关键：隔离层叠上下文，防止内部的 ::before 溢出遮挡文字 */
  z-index: 1;
  overflow: hidden; /* 切掉边框外的渐变 */
}

/* 旋转的渐变光束 */
.nav-item-time-engine::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: conic-gradient(
    from 0deg,
    transparent 70%,
    #f9e0a2 80%,
    #d4af37 100%
  );
  animation: spin-gold 3s linear infinite;
  z-index: -2; /* 放在最底层 */
}

/* 内部遮罩，镂空出 1.5px 的金色发光边框 - 白金毛玻璃效果 */
.nav-item-time-engine::after {
  content: '';
  position: absolute;
  inset: 1.5px; /* 决定了流光边框的粗细 */
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.9) 0%, rgba(253, 246, 235, 0.8) 100%);
  backdrop-filter: blur(8px);
  border-radius: 10px; /* 比外层稍微小一点 */
  z-index: -1;
}

/* 选中时光引擎时的特殊内部发光 */
.nav-item-time-engine:active,
.nav-item-time-engine:focus {
  transform: scale(0.98);
}

@keyframes spin-gold {
  100% {
    transform: rotate(360deg);
  }
}

/* 隐藏侧边栏滚动条 - 保持滚动功能但隐藏滚动条 */
aside::-webkit-scrollbar {
  width: 0;
  height: 0;
  background: transparent;
}

aside {
  scrollbar-width: none;
  -ms-overflow-style: none;
}
</style>
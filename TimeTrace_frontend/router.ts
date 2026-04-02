import { createRouter, createWebHashHistory } from 'vue-router';
import { useAuthStore } from './store';
import Layout from './components/Layout.vue';
import Login from './views/Login.vue';
import Register from './views/Register.vue';
import Gallery from './views/Gallery.vue';
import Workshop from './views/Workshop.vue';
import Dashboard from './views/Dashboard.vue';
import HelpCenter from './views/HelpCenter.vue';
import History from './views/History.vue';
import Onboarding from './views/Onboarding.vue';

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/',
      name: 'Onboarding',
      component: Onboarding,
      meta: { guest: true }
    },
    {
      path: '/login',
      name: 'Login',
      component: Login,
      meta: { guest: true }
    },
    {
      path: '/register',
      name: 'Register',
      component: Register,
      meta: { guest: true }
    },
    // 新增：拦截历史遗留的 /app 跳转，强制重定向到 /dashboard
    {
      path: '/app',
      redirect: '/dashboard'
    },
    // 使用一个虚拟父路由加载 Layout 框架
    {
      path: '/_main', 
      component: Layout,
      meta: { requiresAuth: true },
      children: [
        {
          path: '/dashboard',
          name: 'Dashboard',
          component: Dashboard
        },
        {
          path: '/gallery',
          name: 'Gallery',
          component: Gallery
        },
        {
          path: '/workshop',
          redirect: '/workshop/dustless'
        },
        {
          path: '/workshop/:moduleId',
          name: 'Workshop',
          component: Workshop
        },
        {
          path: '/help-center',
          name: 'HelpCenter',
          component: HelpCenter
        },
        {
          path: '/history',
          name: 'History',
          component: History
        }
      ]
    }
  ]
});

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();
  
  const hasToken = localStorage.getItem('token');
  const isAuthReady = authStore.isAuthenticated;
  
  if (to.meta.requiresAuth && !isAuthReady && !hasToken) {
    next('/login');
  } else if (to.meta.guest && (isAuthReady || hasToken)) {
    // 修复：如果已经登录但访问了导览页或登录页，则直接重定向到主仪表盘
    next('/dashboard');
  } else {
    next();
  }
});

export default router;
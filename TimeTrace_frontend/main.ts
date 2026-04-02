import { createApp } from 'vue';
import { createPinia } from 'pinia';
import App from './App.vue';
import router from './router';

// Font Awesome 配置
import { library } from '@fortawesome/fontawesome-svg-core';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
import { fas } from '@fortawesome/free-solid-svg-icons';
import { far } from '@fortawesome/free-regular-svg-icons';

// 注册所有图标
library.add(fas, far);

const app = createApp(App);

// 注册全局组件
app.component('FontAwesomeIcon', FontAwesomeIcon);

app.use(createPinia());
app.use(router);

app.mount('#app');
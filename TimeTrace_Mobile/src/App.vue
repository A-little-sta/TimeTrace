<script setup lang="ts">
import { onLaunch, onShow, onHide } from "@dcloudio/uni-app";
onLaunch(() => {
  console.log("App Launch");
});
onShow(() => {
  console.log("App Show");
});
onHide(() => {
  console.log("App Hide");
});
</script>

<style lang="scss">
/* 全局样式 */
page {
  /* 雅致白底色，带有一点点温暖的灰度，比纯白更护眼高级 */
  background-color: #FAF8F5; 
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  color: var(--text-main);
  font-size: 28rpx;
  line-height: 1.6;
}

/* 岁月剪影 - 高级定制主题色变量 */
:root {
  /* --- 雅致白体系 (Backgrounds) --- */
  --bg-elegant: #FAF8F5;
  --bg-card: #FFFFFF;

  /* --- 流光金体系 (Primary/Golds) --- */
  --gold-light: #F5E4C3;   /* 高光金 */
  --gold-main: #D4AF37;    /* 经典流光金 */
  --gold-dark: #B58D1F;    /* 沉淀金 */

  /* --- 香槟橙体系 (Accents/Oranges) --- */
  --champagne-light: #FCE8D5; /* 柔和橙 */
  --champagne-main: #F2A97F;  /* 香槟橙 */

  /* --- 文字体系 (Text) --- */
  --text-main: #3D352B;       /* 深褐灰（替代死板的纯黑） */
  --text-muted: #A39B90;      /* 质感灰（未选中状态） */
}

/* 隐藏滚动条 */
::-webkit-scrollbar {
  display: none;
  width: 0;
  height: 0;
}

/* 隐藏原生 TabBar 占位条，只保留自定义悬浮导航栏 */
.uni-tabbar {
  display: none !important;
}

uni-tabbar {
  display: none !important;
}
</style>
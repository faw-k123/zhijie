import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/login',
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('../views/RegisterView.vue'),
    },
    {
      path: '/home',
      name: 'home',
      component: () => import('../views/HomeView.vue'),
      children: [
        {
          path: 'emotion',
          name: 'emotion',
          component: () => import('../views/EmotionOverlayView.vue'),
        },
      ],
    },
    {
      path: '/music-show/:category',
      name: 'music-show',
      component: () => import('../views/MusicShowView.vue'),
    },
    {
      path: '/music/:category/:subcategory',
      name: 'music-detail',
      component: () => import('../views/MusicDetailView.vue'),
    },
    {
      path: '/imagery',
      name: 'imagery',
      component: () => import('../views/MusicSongsView.vue'),
    },
    {
      path: '/promo-report',
      name: 'promo-report',
      component: () => import('../views/PromoReportView.vue'),
    },
    {
      path: '/video-bgm',
      name: 'video-bgm',
      component: () => import('../views/VideoBgmView.vue'),
    },
    {
      path: '/global-effect',
      name: 'global-effect',
      component: () => import('../views/GlobalEffectView.vue'),
    },
    {
      path: '/personality-test',
      name: 'personality-test',
      component: () => import('../views/PersonalityHubView.vue'),
    },
    {
      path: '/profile-center',
      name: 'profile-center',
      component: () => import('../views/ProfileCenterView.vue'),
    },

    {
      path: '/ai-music',
      name: 'ai-music',
      component: () => import('../views/AiMusicView.vue'),
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('../views/AboutView.vue'),
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('../views/ProfileView.vue'),
    },
    {
      path: '/music-display/:id',
      name: 'music-display',
      component: () => import('../views/MusicDisplayView.vue'),
    },
    {
      path: '/private-space',
      name: 'private-space',
      component: () => import('../views/PrivateSpaceView.vue'),
    },
  ],
})

router.beforeEach((to) => {
  const publicPaths = ['/login', '/register']
  // Development-only UI preview; does not create a real authenticated session.
  if (import.meta.env.DEV && to.query.designPreview === '1') {
    sessionStorage.setItem('guoyin:design-preview', '1')
  }
  if (import.meta.env.DEV && to.query.designPreview === '0') {
    sessionStorage.removeItem('guoyin:design-preview')
  }
  const designPreview = import.meta.env.DEV && sessionStorage.getItem('guoyin:design-preview') === '1'
  const loggedIn = !!localStorage.getItem('username')
  if (!publicPaths.includes(to.path) && !loggedIn && !designPreview) {
    return '/login'
  }
  if ((to.path === '/login' || to.path === '/register') && loggedIn) {
    return '/home'
  }
})

export default router

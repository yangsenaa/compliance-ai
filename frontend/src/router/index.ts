import { createRouter, createWebHistory } from 'vue-router'
import Inspector from '@/views/Inspector.vue'
import Advisor from '@/views/Advisor.vue'
import DocManager from '@/views/DocManager.vue'
import Login from '@/views/Login.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: Login,
      meta: { title: '登录', public: true }
    },
    {
      path: '/',
      redirect: '/inspector'
    },
    {
      path: '/inspector',
      name: 'inspector',
      component: Inspector,
      meta: { title: '质检官' }
    },
    {
      path: '/advisor',
      name: 'advisor',
      component: Advisor,
      meta: { title: '答疑官' }
    },
    {
      path: '/docs',
      name: 'docs',
      component: DocManager,
      meta: { title: '文档管理' }
    }
  ]
})

// 路由守卫：未登录跳登录页
router.beforeEach((to) => {
  if (to.meta.public) return true
  const raw = localStorage.getItem('compliance_ai_auth')
  const auth = raw ? JSON.parse(raw) : null
  if (!auth?.role) {
    return { name: 'login' }
  }
  return true
})

export default router

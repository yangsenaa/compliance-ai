import { createRouter, createWebHistory } from 'vue-router'
import Inspector from '@/views/Inspector.vue'
import Advisor from '@/views/Advisor.vue'
import DocManager from '@/views/DocManager.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
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

export default router

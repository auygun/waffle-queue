import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/queue',
    },
    {
      path: '/queue',
      name: 'queue',
      props: (route) => ({ offset: route.query.offset }),
      component: () => import('../views/QueueView.vue'),
    },
    {
      path: '/request',
      name: 'request',
      component: () => import('../views/RequestView.vue'),
    },
    {
      path: '/log',
      name: 'log',
      component: () => import('../views/LogView.vue'),
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('../views/AboutView.vue'),
    },
  ],
})

export default router

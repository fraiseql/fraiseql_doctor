import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      // route level code-splitting
      // this generates a separate chunk (Dashboard.[hash].js) for this route
      // which is lazy-loaded when the route is visited.
      component: () => import('../views/Dashboard.vue'),
    },
    {
      path: '/endpoints',
      name: 'endpoints',
      component: () => import('../views/Endpoints.vue'),
    },
    {
      path: '/endpoints/new',
      name: 'endpoint-new',
      component: () => import('../views/EndpointNew.vue'),
    },
    {
      path: '/endpoints/:id',
      name: 'endpoint-details',
      component: () => import('../views/EndpointDetailsView.vue'),
      props: true,
    },
    {
      path: '/endpoints/:id/edit',
      name: 'endpoint-edit',
      component: () => import('../views/EndpointEdit.vue'),
      props: true,
    },
  ],
})

export default router
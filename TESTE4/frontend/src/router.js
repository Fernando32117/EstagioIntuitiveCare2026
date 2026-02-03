import { createRouter, createWebHistory } from 'vue-router'
import OperadorasList from './views/OperadorasList.vue'
import OperadoraDetails from './views/OperadoraDetails.vue'

const routes = [
  {
    path: '/',
    name: 'operadoras',
    component: OperadorasList
  },
  {
    path: '/operadora/:cnpj',
    name: 'operadora-details',
    component: OperadoraDetails,
    props: true
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router

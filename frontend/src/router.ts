import { createRouter, createWebHistory } from 'vue-router'
import ProjectsPage from './pages/ProjectsPage.vue'
import WritePage from './pages/WritePage.vue'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'projects', component: ProjectsPage },
    { path: '/projects/:id/write', name: 'write', component: WritePage, props: true },
  ],
})
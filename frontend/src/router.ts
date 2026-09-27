import { createRouter, createWebHistory } from 'vue-router'
import ProjectsPage from './pages/ProjectsPage.vue'
import WritePage from './pages/WritePage.vue'
import IntentPage from './pages/IntentPage.vue'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'projects', component: ProjectsPage },
    { path: '/projects/:id/intent', name: 'intent', component: IntentPage, props: true },
    { path: '/projects/:id/write', name: 'write', component: WritePage, props: true },
  ],
})
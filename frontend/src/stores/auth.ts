import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userId = ref(localStorage.getItem('userId') || '')
  const username = ref(localStorage.getItem('username') || '')

  function persistUser(data: { token: string; id?: string; username?: string }) {
    token.value = data.token
    if (data.id) userId.value = data.id
    if (data.username) username.value = data.username
    localStorage.setItem('token', data.token)
    localStorage.setItem('userId', userId.value)
    localStorage.setItem('username', username.value)
  }

  async function register(user: string, _pass: string) {
    // 当前后端暂无 /auth/* 端点 → mock 直接成功
    persistUser({ token: 'mock-token-' + Date.now(), id: '1', username: user })
  }

  async function login(user: string, _pass: string) {
    // 当前后端暂无 /auth/* 端点 → mock 直接成功
    persistUser({ token: 'mock-token-' + Date.now(), id: '1', username: user })
  }

  function logout() {
    token.value = ''
    userId.value = ''
    username.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('userId')
    localStorage.removeItem('username')
  }

  return { token, userId, username, register, login, logout }
})

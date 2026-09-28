import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userId = ref(localStorage.getItem('userId') || '')
  const username = ref(localStorage.getItem('username') || '')

  function persistUser(data: { token: string; user_id?: string | number; username?: string }) {
    token.value = data.token
    if (data.user_id !== undefined) userId.value = String(data.user_id)
    if (data.username) username.value = data.username
    localStorage.setItem('token', data.token)
    localStorage.setItem('userId', userId.value)
    localStorage.setItem('username', username.value)
  }

  async function register(user: string, pass: string) {
    const { data } = await api.post('/auth/register', {
      username: user,
      password: pass
    })
    persistUser(data)
  }

  async function login(user: string, pass: string) {
    const { data } = await api.post('/auth/login', {
      username: user,
      password: pass
    })
    persistUser(data)
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

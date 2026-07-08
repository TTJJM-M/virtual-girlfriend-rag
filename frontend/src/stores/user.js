import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, register as registerApi, getMe, changePassword as changePasswordApi } from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  const user = ref(null)
  const token = ref(localStorage.getItem('access_token'))

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  async function login(credentials) {
    const { data } = await loginApi(credentials)
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    token.value = data.access_token
    user.value = data.user
    return data
  }

  async function register(userData) {
    const { data } = await registerApi(userData)
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    token.value = data.access_token
    user.value = data.user
    return data
  }

  async function fetchUser() {
    try {
      const { data } = await getMe()
      user.value = data
    } catch {
      logout()
    }
  }

  async function changePassword(passwords) {
    await changePasswordApi(passwords)
  }

  function logout() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    token.value = null
    user.value = null
  }

  // Initialize user from token if exists
  if (token.value) {
    fetchUser()
  }

  return { user, token, isLoggedIn, isAdmin, login, register, fetchUser, changePassword, logout }
})

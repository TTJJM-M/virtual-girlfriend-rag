import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getSessions, createSession, deleteSession as deleteSessionApi } from '@/api/chat'

export const useSessionStore = defineStore('session', () => {
  const sessions = ref([])
  const currentSessionId = ref(null)

  async function fetchSessions() {
    const { data } = await getSessions()
    sessions.value = data
  }

  async function createNewSession(title) {
    const { data } = await createSession({ title })
    sessions.value.unshift(data)
    currentSessionId.value = data.id
    return data
  }

  async function deleteSession(id) {
    await deleteSessionApi(id)
    sessions.value = sessions.value.filter(s => s.id !== id)
    if (currentSessionId.value === id) {
      currentSessionId.value = null
    }
  }

  function setCurrentSession(id) {
    currentSessionId.value = id
  }

  return { sessions, currentSessionId, fetchSessions, createNewSession, deleteSession, setCurrentSession }
})

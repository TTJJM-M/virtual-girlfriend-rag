import api from './request'

export function getSessions() {
  return api.get('/sessions')
}

export function createSession(data) {
  return api.post('/sessions', data)
}

export function deleteSession(sessionId) {
  return api.delete(`/sessions/${sessionId}`)
}

export function getMessages(sessionId) {
  return api.get(`/sessions/${sessionId}/messages`)
}

export function sendMessage(sessionId, message, onChunk) {
  return new Promise((resolve, reject) => {
    const token = localStorage.getItem('access_token')

    fetch(`/api/chat/${sessionId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ message, stream: true }),
    })
      .then((res) => {
        if (!res.ok) throw new Error('Network response was not ok')
        const reader = res.body.getReader()
        const decoder = new TextDecoder()

        function read() {
          reader.read().then(({ done, value }) => {
            if (done) {
              resolve()
              return
            }

            const chunk = decoder.decode(value)
            const lines = chunk.split('\n')

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const data = line.slice(6)
                if (data === '[DONE]') {
                  resolve()
                  return
                }

                try {
                  const event = JSON.parse(data)
                  onChunk(event)
                } catch {
                  // Ignore parse errors
                }
              }
            }

            read()
          })
        }

        read()
      })
      .catch(reject)
  })
}

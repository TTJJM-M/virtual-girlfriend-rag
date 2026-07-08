import api from './request'

export function getDocuments() {
  return api.get('/knowledge')
}

export function uploadDocument(file) {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/knowledge/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
}

export function deleteDocument(id) {
  return api.delete(`/knowledge/${id}`)
}

export function getDocumentStatus(id) {
  return api.get(`/knowledge/${id}/status`)
}

export function getKnowledgeStats() {
  return api.get('/knowledge/stats')
}

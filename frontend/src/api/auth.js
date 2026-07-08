import api from './request'

export function login(data) {
  return api.post('/auth/login', data)
}

export function register(data) {
  return api.post('/auth/register', data)
}

export function refreshToken(data) {
  return api.post('/auth/refresh', data)
}

export function changePassword(data) {
  return api.put('/auth/password', data)
}

export function getMe() {
  return api.get('/auth/me')
}

import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('auth_token')
  if(token){ config.headers['Authorization'] = `Token ${token}` }
  return config
})

export function setAuthToken(token){
  if(token){ localStorage.setItem('auth_token', token) }
}

export function clearAuthToken(){
  localStorage.removeItem('auth_token')
}

export default api

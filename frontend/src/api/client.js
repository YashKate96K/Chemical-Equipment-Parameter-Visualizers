import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
})

api.interceptors.request.use(config => {
  // TEMPORARY BYPASS: Don't send authentication headers
  // const token = localStorage.getItem('auth_token')
  // const url = config.url || ''
  // const isAuthEndpoint = url.includes('/auth/token/') || url.includes('/auth/register/')
  // if (token && !isAuthEndpoint) {
  //   config.headers['Authorization'] = `Token ${token}`
  // }
  
  // No authentication headers needed for testing
  return config
})

api.interceptors.response.use(
  response => response,
  error => {
    // TEMPORARY BYPASS: Don't redirect on 401 errors
    // const status = error?.response?.status
    // const detail = error?.response?.data?.detail
    // if (status === 401 && detail === 'Invalid token.') {
    //   try {
    //     localStorage.removeItem('auth_token')
    //   } catch {}
    //   try {
    //     sessionStorage.removeItem('session_authed')
    //   } catch {}
    //   if (typeof window !== 'undefined') {
    //     window.location.assign('/signin')
    //   }
    // }
    return Promise.reject(error)
  }
)

export function setAuthToken(token){
  if(token){ localStorage.setItem('auth_token', token) }
}

export function clearAuthToken(){
  localStorage.removeItem('auth_token')
}

export default api

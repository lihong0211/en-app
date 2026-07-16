import axios from 'axios'

const http = axios.create({
  baseURL: process.env.VUE_APP_API_BASE_URL
})

http.interceptors.request.use(async (config) => {
  const token = await window.electronAPI.getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use((response) => {
  if (response.data && response.data.code === 401) {
    window.electronAPI.clearToken()
    window.electronAPI.sessionExpired()
  }
  return response
})

export default http

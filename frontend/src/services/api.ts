import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器：注入 Token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：处理错误
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // 当前后端暂无 auth，401 只在特殊路由上有效；这里仅清理 token，不强跳 login
    // （避免接口未实现时登录页↔首页循环跳转）
    return Promise.reject(error)
  }
)

export default api

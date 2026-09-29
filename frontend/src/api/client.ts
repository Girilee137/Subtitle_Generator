import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { API_URL } from '@/lib/config'
import { useAuthStore } from '@/stores/authStore'
import type { TokenPair } from '@/types/api'

export const apiClient = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
})

apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

type RetryConfig = InternalAxiosRequestConfig & { _retry?: boolean }

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as RetryConfig | undefined
    const refreshToken = useAuthStore.getState().refreshToken
    if (error.response?.status === 401 && original && !original._retry && refreshToken) {
      original._retry = true
      try {
        const response = await axios.post<TokenPair>(`${API_URL}/api/v1/auth/refresh`, {
          refresh_token: refreshToken,
        })
        useAuthStore
          .getState()
          .setSession(response.data.access_token, response.data.refresh_token, response.data.user)
        original.headers.Authorization = `Bearer ${response.data.access_token}`
        return apiClient(original)
      } catch {
        useAuthStore.getState().clearSession()
      }
    }
    return Promise.reject(error)
  },
)


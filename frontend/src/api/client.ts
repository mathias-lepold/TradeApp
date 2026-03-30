import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 12_000,
  headers: { 'Content-Type': 'application/json' },
})

// Global response interceptor — logt Fehler, wirft weiter
apiClient.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err.response?.data?.detail ?? err.message ?? 'Unbekannter Fehler'
    console.error(`[API] ${err.config?.method?.toUpperCase()} ${err.config?.url} → ${msg}`)
    return Promise.reject(new Error(msg))
  }
)

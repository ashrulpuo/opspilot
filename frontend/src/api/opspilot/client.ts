/**
 * OpsPilot API Client
 * Axios-based HTTP client with interceptors for authentication
 */

import axios, { type AxiosError, type AxiosRequestConfig, type AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'
import { useOpsPilotAuthStore } from '@/stores/modules/opspilot'

/**
 * VITE_API_URL must be the API **origin** only (e.g. http://127.0.0.1:8000), with no `/api` or `/api/v1` suffix.
 * If unset: use the **page origin** whenever the hostname is not loopback (localhost / 127.0.0.1). That covers
 * production static builds and **Vite dev behind Caddy/TLS** (`https://your.domain` → `/api` on the same host).
 * Only fall back to `http://127.0.0.1:8000` for typical local dev (`localhost:8848`) or non-browser contexts.
 */
function isLoopbackHostname(hostname: string): boolean {
  const h = hostname.toLowerCase()
  return h === 'localhost' || h === '127.0.0.1' || h === '[::1]' || h.endsWith('.localhost')
}

function normalizeApiOrigin(raw: string): string {
  let u = raw.trim().replace(/\/+$/, '')
  const lower = u.toLowerCase()
  if (lower.endsWith('/api/v1')) {
    u = u.slice(0, -'/api/v1'.length)
  } else if (lower.endsWith('/api')) {
    u = u.slice(0, -'/api'.length)
  }
  return u.replace(/\/+$/, '')
}

function resolveApiOriginRaw(): string {
  const fromEnv = (import.meta.env.VITE_API_URL as string | undefined)?.trim()
  if (fromEnv) {
    return fromEnv
  }
  if (typeof window !== 'undefined' && window.location?.hostname) {
    if (!isLoopbackHostname(window.location.hostname)) {
      return window.location.origin
    }
  }
  if (import.meta.env.DEV) {
    return 'http://127.0.0.1:8000'
  }
  return 'http://127.0.0.1:8000'
}

const API_BASE_URL = normalizeApiOrigin(resolveApiOriginRaw())
const API_VERSION = 'v1'
const BASE_URL = `${API_BASE_URL}/api/${API_VERSION}`

// Request config interface
export interface CustomAxiosRequestConfig extends AxiosRequestConfig {
  skipAuth?: boolean
  skipRefresh?: boolean
  /** When true, response errors are rejected without ElMessage (caller shows context-specific text). */
  suppressGlobalErrorToast?: boolean
}

// Pending requests map for cancellation
const pendingMap = new Map<string, AbortController>()

/**
 * Get unique identifier for request
 */
const getPendingUrl = (config: CustomAxiosRequestConfig): string => {
  const { method, url, params, data } = config
  return [method, url, JSON.stringify(params), JSON.stringify(data)].join('&')
}

/**
 * Cancel duplicate requests
 */
const addPending = (config: CustomAxiosRequestConfig): void => {
  removePending(config)
  const url = getPendingUrl(config)
  const controller = new AbortController()
  config.signal = controller.signal
  pendingMap.set(url, controller)
}

const removePending = (config: CustomAxiosRequestConfig): void => {
  const url = getPendingUrl(config)
  const controller = pendingMap.get(url)
  if (controller) {
    controller.abort()
    pendingMap.delete(url)
  }
}

/**
 * Axios instance for OpsPilot API
 */
const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * Request interceptor
 * - Attach JWT token
 * - Cancel duplicate requests
 */
apiClient.interceptors.request.use(
  (config: CustomAxiosRequestConfig): CustomAxiosRequestConfig => {
    // Cancel duplicate requests
    if (!config.skipRefresh) {
      addPending(config)
    }

    // Attach auth token
    if (!config.skipAuth) {
      const authStore = useOpsPilotAuthStore()
      const token = authStore.accessToken
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`
      }
    }

    return config
  },
  (error: AxiosError): Promise<AxiosError> => {
    return Promise.reject(error)
  }
)

/**
 * Response interceptor
 * - Handle errors
 * - Refresh token on 401
 * - Show error messages
 */
apiClient.interceptors.response.use(
  (response: AxiosResponse): AxiosResponse => {
    const config = response.config as CustomAxiosRequestConfig

    // Remove from pending map
    if (!config.skipRefresh) {
      removePending(config)
    }

    // Backend returns data directly, not wrapped in ApiResponse
    // Just return response as-is
    return response
  },
  async (error: AxiosError): Promise<AxiosError> => {
    const config = error.config as CustomAxiosRequestConfig

    // Remove from pending map
    if (config && !config.skipRefresh) {
      removePending(config)
    }

    const suppressToast = Boolean(config?.suppressGlobalErrorToast)

    // Handle 401 Unauthorized
    if (error.response?.status === 401) {
      const authStore = useOpsPilotAuthStore()

      // Skip auth refresh if already refreshing or this is a refresh request
      if (!config?.skipRefresh) {
        try {
          // Try to refresh token
          const refreshToken = authStore.refreshToken
          if (refreshToken) {
            const newToken = await refreshAccessToken(refreshToken)
            if (newToken) {
              authStore.updateToken(newToken)
              // Retry original request
              if (config) {
                config.skipAuth = true
                config.headers.Authorization = `Bearer ${newToken}`
                return apiClient.request(config)
              }
            }
          }
        } catch (refreshError) {
          console.error('Token refresh failed:', refreshError)
        }
      }

      // Logout and redirect to login
      await authStore.logout()
      if (typeof window !== 'undefined') {
        window.location.href = '/login'
      }
      return Promise.reject(error)
    }

    // FastAPI: detail may be a string, or a list of validation errors { loc, msg, ... }[]
    const formatFastApiDetail = (data: unknown): string | undefined => {
      const detail = (data as { detail?: unknown })?.detail
      if (typeof detail === 'string') {
        return detail
      }
      if (Array.isArray(detail)) {
        const parts = detail.map((item: { msg?: string }) => item.msg).filter((m): m is string => Boolean(m))
        return parts.length ? parts.join(' ') : undefined
      }
      return undefined
    }

    // Handle other errors
    const data = error.response?.data as { detail?: unknown; message?: string } | undefined
    const fromServer = formatFastApiDetail(data) || data?.message
    const errorMessage = fromServer || error.message || 'Network error occurred'

    if (!suppressToast) {
      if (error.response?.status === 403) {
        ElMessage.error(fromServer ?? 'Access denied. You do not have permission to perform this action.')
      } else if (error.response?.status === 404) {
        ElMessage.error(fromServer ?? 'Resource not found.')
      } else if (error.response?.status === 500) {
        ElMessage.error(fromServer ?? 'Internal server error. Please try again later.')
      } else if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        ElMessage.error('Request timeout. Please check your connection and try again.')
      } else if (!error.response) {
        ElMessage.error('Network error. Please check your connection.')
      } else {
        ElMessage.error(errorMessage)
      }
    }

    return Promise.reject(error)
  }
)

/**
 * Refresh access token
 */
const refreshAccessToken = async (refreshToken: string): Promise<string | null> => {
  try {
    const response = await axios.post<{ access_token: string }>(`${API_BASE_URL}/api/v1/auth/refresh`, {
      refresh_token: refreshToken,
    })
    return response.data.access_token
  } catch (error) {
    return null
  }
}

/**
 * API client methods
 */
const request = {
  get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return apiClient.get(url, config).then(res => res.data)
  },

  post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return apiClient.post(url, data, config).then(res => res.data)
  },

  put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return apiClient.put(url, data, config).then(res => res.data)
  },

  patch<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return apiClient.patch(url, data, config).then(res => res.data)
  },

  delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return apiClient.delete(url, config).then(res => res.data)
  },
}

export default request
export { apiClient, BASE_URL, API_BASE_URL }

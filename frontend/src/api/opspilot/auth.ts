/**
 * OpsPilot Auth API
 * Authentication endpoints
 */

import request from './client'
import type { CustomAxiosRequestConfig } from './client'
import type {
  LoginRequest,
  RegisterRequest,
  BootstrapRequest,
  ForgotPasswordRequest,
  ResetPasswordRequest,
  LoginResponse,
  SetupRequiredResponse,
  User,
} from './types'

export const AuthAPI = {
  /**
   * True when there are no users yet (show initial setup wizard).
   */
  getSetupRequired: (): Promise<SetupRequiredResponse> => {
    return request.get<SetupRequiredResponse>('/auth/setup-required', {
      skipAuth: true,
    } as CustomAxiosRequestConfig)
  },

  /**
   * Create first admin (only when database has zero users).
   */
  bootstrap: (data: BootstrapRequest): Promise<LoginResponse> => {
    return request.post<LoginResponse>('/auth/bootstrap', data, {
      skipAuth: true,
    } as CustomAxiosRequestConfig)
  },

  /**
   * User login
   */
  login: (credentials: LoginRequest): Promise<LoginResponse> => {
    return request.post<LoginResponse>('/auth/login', credentials)
  },

  /**
   * User registration
   */
  register: (data: RegisterRequest): Promise<void> => {
    return request.post<void>('/auth/register', data)
  },

  /**
   * Forgot password - send reset email
   */
  forgotPassword: (data: ForgotPasswordRequest): Promise<void> => {
    return request.post<void>('/auth/forgot-password', data)
  },

  /**
   * Reset password with token
   */
  resetPassword: (data: ResetPasswordRequest): Promise<void> => {
    return request.post<void>('/auth/reset-password', data)
  },

  /**
   * Refresh access token
   */
  refreshToken: (refreshToken: string): Promise<{ access_token: string }> => {
    return request.post<{ access_token: string }>('/auth/refresh', { refresh_token: refreshToken })
  },

  /**
   * Logout current user
   */
  logout: (): Promise<void> => {
    return request.post<void>('/auth/logout')
  },

  /**
   * Get current user info
   */
  getCurrentUser: (): Promise<User> => {
    return request.get<User>('/auth/me')
  },

  /**
   * Update current user profile
   */
  updateProfile: (data: { full_name?: string; avatar_url?: string }): Promise<User> => {
    return request.put<User>('/auth/me', data)
  },

  /**
   * Change password
   */
  changePassword: (data: { current_password: string; new_password: string }): Promise<void> => {
    return request.post<void>('/auth/change-password', data)
  },
}

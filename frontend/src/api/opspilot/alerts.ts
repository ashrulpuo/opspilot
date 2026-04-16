/**
 * OpsPilot Alerts API
 * Alert management endpoints
 */

import request from '../opspilot/client'
import type { Alert, AlertStats, CreateAlertRequest, PaginatedResponse } from './types'

export const AlertsAPI = {
  /**
   * Get all alerts for current organization
   */
  list: (params?: {
    page?: number
    page_size?: number
    server_id?: string
    severity?: string
    resolved?: boolean
    start?: string
    end?: string
  }): Promise<PaginatedResponse<Alert>> => {
    return request.get<PaginatedResponse<Alert>>('/alerts', { params })
  },

  /**
   * Get alert by ID
   */
  get: (id: string): Promise<Alert> => {
    return request.get<Alert>(`/alerts/${id}`)
  },

  /**
   * Create new alert
   */
  create: (data: CreateAlertRequest): Promise<Alert> => {
    return request.post<Alert>('/alerts', data)
  },

  /**
   * Update alert
   */
  update: (id: string, data: Partial<CreateAlertRequest>): Promise<Alert> => {
    return request.put<Alert>(`/alerts/${id}`, data)
  },

  /**
   * Delete alert
   */
  delete: (id: string): Promise<void> => {
    return request.delete<void>(`/alerts/${id}`)
  },

  /**
   * Resolve alert
   */
  resolve: (id: string): Promise<Alert> => {
    return request.post<Alert>(`/alerts/${id}/resolve`)
  },

  /**
   * Get alert statistics
   */
  getStats: (params?: { start?: string; end?: string }): Promise<AlertStats> => {
    return request.get<AlertStats>('/alerts/stats', { params })
  },
}

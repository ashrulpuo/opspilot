/**
 * OpsPilot Logs API
 * Log management endpoints
 */

import request from '../opspilot/client'
import type { Log, LogStats, PaginatedResponse } from './types'

export const LogsAPI = {
  /**
   * Query logs with search or filters
   */
  query: (params?: {
    query?: string
    log_levels?: string[]
    start_time?: string
    end_time?: string
    max_results?: number
  }): Promise<{ total: number; logs: Log[]; max_results: number }> => {
    return request.post<{ total: number; logs: Log[]; max_results: number }>('/logs/query', params)
  },

  /**
   * Get all logs for current organization
   */
  list: (
    organizationId: string,
    params?: {
      page?: number
      page_size?: number
      server_id?: string
      log_level?: string
      log_type?: string
      start_date?: string
      end_date?: string
    }
  ): Promise<PaginatedResponse<Log>> => {
    return request.get<PaginatedResponse<Log>>(`/organizations/${organizationId}/logs`, { params })
  },

  /**
   * Get log by ID
   */
  get: (organizationId: string, logId: string): Promise<Log> => {
    return request.get<Log>(`/organizations/${organizationId}/logs/${logId}`)
  },

  /**
   * Get log statistics
   */
  getStats: (
    organizationId: string,
    params?: {
      time_range?: string
      server_id?: string
    }
  ): Promise<LogStats> => {
    return request.get<LogStats>(`/organizations/${organizationId}/logs/stats`, { params })
  },

  /**
   * Stream logs in real-time (placeholder)
   */
  stream: (
    organizationId: string,
    params?: {
      server_id?: string
      log_level?: string
    }
  ): Promise<{
    message: string
    organization_id: string
    server_id?: string
    log_level?: string
    note: string
  }> => {
    return request.get<{
      message: string
      organization_id: string
      server_id?: string
      log_level?: string
      note: string
    }>(`/organizations/${organizationId}/logs/stream`, { params })
  },
}

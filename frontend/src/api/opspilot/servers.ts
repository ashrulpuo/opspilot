/**
 * OpsPilot Servers API
 * Server management endpoints
 */

import request from './client'
import type { Server, CreateServerRequest, UpdateServerRequest, ApplyStateRequest, ApplyStateResponse } from './types'

export const ServersAPI = {
  /**
   * Get all servers for an organization
   */
  list: (
    organizationId: string,
    params?: { skip?: number; limit?: number }
  ): Promise<{ total: number; servers: Server[] }> => {
    return request.get<{ total: number; servers: Server[] }>(`/organizations/${organizationId}/servers`, { params })
  },

  /**
   * Get server by ID
   */
  get: (id: string): Promise<Server> => {
    return request.get<Server>(`/servers/${id}`)
  },

  /**
   * Create new server
   */
  create: (organizationId: string, data: CreateServerRequest): Promise<Server> => {
    return request.post<Server>(`/organizations/${organizationId}/servers`, data)
  },

  /**
   * Update server
   */
  update: (id: string, data: UpdateServerRequest): Promise<Server> => {
    return request.put<Server>(`/servers/${id}`, data)
  },

  /**
   * Delete server
   */
  delete: (id: string): Promise<void> => {
    return request.delete<void>(`/servers/${id}`)
  },

  /**
   * Apply Salt state to server
   */
  applyState: (id: string, data: ApplyStateRequest): Promise<ApplyStateResponse> => {
    return request.post<ApplyStateResponse>(`/servers/${id}/states/apply`, data)
  },

  /**
   * Collect metrics from server
   */
  collectMetrics: (id: string): Promise<{ server_id: string; metrics: any }> => {
    return request.get<{ server_id: string; metrics: any }>(`/servers/${id}/metrics`)
  },

  /**
   * Execute backup on server
   */
  executeBackup: (id: string): Promise<{ server_id: string; backup_result: any }> => {
    return request.post<{ server_id: string; backup_result: any }>(`/servers/${id}/backups/execute`)
  },

  /**
   * Perform health check on server
   */
  performHealthCheck: (id: string): Promise<{ server_id: string; overall_status: string; checks: any }> => {
    return request.post<{ server_id: string; overall_status: string; checks: any }>(`/servers/${id}/health/check`)
  },

  /**
   * Get metrics history for server
   */
  getMetricsHistory: (id: string, hours?: number): Promise<any> => {
    return request.get<any>(`/servers/${id}/metrics/history`, { params: { hours } })
  },

  /**
   * Get backups for server
   */
  getBackups: (id: string, limit?: number): Promise<any> => {
    return request.get<any>(`/servers/${id}/backups`, { params: { limit } })
  },

  /**
   * Get health history for server
   */
  getHealthHistory: (id: string, hours?: number): Promise<any> => {
    return request.get<any>(`/servers/${id}/health/history`, { params: { hours } })
  },
}

/**
 * OpsPilot Servers API
 * Server management endpoints
 */

import request from './client'
import type {
  Server,
  CreateServerRequest,
  UpdateServerRequest,
  ApplyStateRequest,
  ApplyStateResponse,
  ServerOverviewPanel,
  SaltServiceStateRow,
  SaltProcessRow,
} from './types'

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
   * Re-queue SSH Salt minion install (stored SSH creds, Linux only).
   */
  reinstallSaltMinion: (id: string): Promise<Server> => {
    return request.post<Server>(`/servers/${id}/reinstall-salt-minion`)
  },

  redeployAgent: (id: string): Promise<Server> => {
    return request.post<Server>(`/servers/${id}/redeploy-agent`)
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

  /** Overview tab: gauges + counts + recent Salt events (JWT). */
  getOverviewPanel: (id: string): Promise<ServerOverviewPanel> => {
    return request.get<ServerOverviewPanel>(`/servers/${id}/overview-panel`)
  },

  getSaltServices: (id: string): Promise<SaltServiceStateRow[]> => {
    return request.get<SaltServiceStateRow[]>(`/servers/${id}/salt/services`)
  },

  getSaltProcesses: (id: string): Promise<SaltProcessRow[]> => {
    return request.get<SaltProcessRow[]>(`/servers/${id}/salt/processes`)
  },

  getHostInfo: (id: string): Promise<any> => {
    return request.get<any>(`/servers/${id}/host-info`)
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

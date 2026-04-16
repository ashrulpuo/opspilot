/**
 * OpsPilot Metrics API
 * Metrics collection and retrieval endpoints
 */

import request from './client'

export const MetricsAPI = {
  /**
   * Get latest metrics for server
   */
  getServerMetrics: (serverId: string): Promise<{ server_id: string; metrics: any }> => {
    return request.get<{ server_id: string; metrics: any }>(`/servers/${serverId}/metrics`)
  },

  /**
   * Get metrics history for server
   */
  getServerMetricsHistory: (serverId: string, hours: number = 24): Promise<any> => {
    return request.get<any>(`/servers/${serverId}/metrics/history`, { params: { hours } })
  },

  /**
   * Get metrics summary for organization
   */
  getOrganizationMetricsSummary: (organizationId: string): Promise<any> => {
    return request.get<any>(`/organizations/${organizationId}/metrics/summary`)
  },

  /**
   * Ingest metrics (called by Salt agent)
   */
  ingestMetrics: (
    serverId: string,
    data: { server_id: string; organization_id: string; metrics: any }
  ): Promise<any> => {
    return request.post<any>(`/servers/${serverId}/metrics`, data)
  },
}

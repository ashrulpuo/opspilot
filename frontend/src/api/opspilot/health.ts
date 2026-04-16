/**
 * OpsPilot Health Checks API
 * Health monitoring endpoints
 */

import request from './client'

export const HealthChecksAPI = {
  /**
   * Perform health check on server
   */
  performCheck: (serverId: string): Promise<{ server_id: string; overall_status: string; checks: any }> => {
    return request.post<{ server_id: string; overall_status: string; checks: any }>(`/servers/${serverId}/health/check`)
  },

  /**
   * Get health history for server
   */
  getServerHealthHistory: (serverId: string, hours: number = 24): Promise<any> => {
    return request.get<any>(`/servers/${serverId}/health/history`, { params: { hours } })
  },

  /**
   * Get health summary for organization
   */
  getOrganizationHealthSummary: (organizationId: string): Promise<any> => {
    return request.get<any>(`/organizations/${organizationId}/health/summary`)
  },

  /**
   * Ingest health report (called by Salt agent)
   */
  ingestHealthReport: (
    serverId: string,
    data: { server_id: string; organization_id: string; checks: any }
  ): Promise<any> => {
    return request.post<any>(`/servers/${serverId}/health`, data)
  },
}

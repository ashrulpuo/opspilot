/**
 * OpsPilot Backups API
 * Backup management endpoints
 */

import request from './client'

export const BackupsAPI = {
  /**
   * Execute backup on server
   */
  execute: (serverId: string): Promise<{ server_id: string; backup_result: any }> => {
    return request.post<{ server_id: string; backup_result: any }>(`/servers/${serverId}/backups/execute`)
  },

  /**
   * Get backup history for server
   */
  getServerBackups: (serverId: string, limit: number = 10): Promise<any> => {
    return request.get<any>(`/servers/${serverId}/backups`, { params: { limit } })
  },

  /**
   * Get backup details
   */
  getBackupDetails: (serverId: string, backupId: string): Promise<any> => {
    return request.get<any>(`/servers/${serverId}/backups/${backupId}`)
  },

  /**
   * Restore backup
   */
  restore: (serverId: string, backupId: string): Promise<any> => {
    return request.post<any>(`/servers/${serverId}/backups/${backupId}/restore`)
  },

  /**
   * Get backup summary for organization
   */
  getOrganizationBackupsSummary: (organizationId: string): Promise<any> => {
    return request.get<any>(`/organizations/${organizationId}/backups/summary`)
  },

  /**
   * Ingest backup report (called by Salt agent)
   */
  ingestBackupReport: (
    serverId: string,
    data: { server_id: string; organization_id: string; backup_results: any }
  ): Promise<any> => {
    return request.post<any>(`/servers/${serverId}/backups`, data)
  },
}

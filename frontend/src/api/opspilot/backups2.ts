/**
 * OpsPilot Backups API
 * Backup management endpoints
 */

import request from '../opspilot/client'
import type { BackupSchedule, BackupHistory, PaginatedResponse } from './types'

export const BackupsAPI = {
  /**
   * Get all backup schedules for current organization
   */
  listSchedules: (params?: {
    page?: number
    page_size?: number
    server_id?: string
    enabled_only?: boolean
  }): Promise<PaginatedResponse<BackupSchedule>> => {
    return request.get<PaginatedResponse<BackupSchedule>>('/backup-schedules', { params })
  },

  /**
   * Get backup schedule by ID
   */
  getSchedule: (id: string): Promise<BackupSchedule> => {
    return request.get<BackupSchedule>(`/backup-schedules/${id}`)
  },

  /**
   * Create new backup schedule
   */
  createSchedule: (
    organizationId: string,
    data: {
      server_id: string
      name: string
      source_paths: string[]
      destination: string
      schedule_type: 'hourly' | 'daily' | 'weekly' | 'monthly'
      schedule_value?: number
      retention_days: number
      enabled: boolean
      compress?: boolean
      encrypt?: boolean
      description?: string
    }
  ): Promise<BackupSchedule> => {
    return request.post<BackupSchedule>(`/organizations/${organizationId}/backup-schedules`, data)
  },

  /**
   * Update backup schedule
   */
  updateSchedule: (
    id: string,
    data: {
      name?: string
      source_paths?: string[]
      destination?: string
      schedule_type?: 'hourly' | 'daily' | 'weekly' | 'monthly'
      schedule_value?: number
      retention_days?: number
      enabled?: boolean
      compress?: boolean
      encrypt?: boolean
      description?: string
    }
  ): Promise<BackupSchedule> => {
    return request.put<BackupSchedule>(`/backup-schedules/${id}`, data)
  },

  /**
   * Delete backup schedule
   */
  deleteSchedule: (id: string): Promise<void> => {
    return request.delete<void>(`/backup-schedules/${id}`)
  },

  /**
   * Run backup immediately
   */
  runBackup: (data: {
    server_id: string
    backup_schedule_id?: string
  }): Promise<{ message: string; server_id: string }> => {
    return request.post<{ message: string; server_id: string }>('/backups/run', data)
  },

  /**
   * Get backup history
   */
  listHistory: (params?: {
    page?: number
    page_size?: number
    server_id?: string
    status_filter?: string
    start_date?: string
    end_date?: string
  }): Promise<PaginatedResponse<BackupHistory>> => {
    return request.get<PaginatedResponse<BackupHistory>>('/backup-history', { params })
  },

  /**
   * Get backup by ID
   */
  getBackup: (id: string): Promise<BackupHistory> => {
    return request.get<BackupHistory>(`/backups/${id}`)
  },
}

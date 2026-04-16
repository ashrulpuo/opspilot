/**
 * OpsPilot Credentials API
 * Credential management endpoints
 */

import request from '../opspilot/client'
import type { Credential, PaginatedResponse } from './types'

export const CredentialsAPI = {
  /**
   * Get all credentials for current organization
   */
  list: (params?: {
    page?: number
    page_size?: number
    server_id?: string
    credential_type?: string
  }): Promise<PaginatedResponse<Credential>> => {
    return request.get<PaginatedResponse<Credential>>('/credentials', { params })
  },

  /**
   * Get credential by ID
   */
  get: (id: string): Promise<Credential> => {
    return request.get<Credential>(`/credentials/${id}`)
  },

  /**
   * Create new credential
   */
  create: (
    organizationId: string,
    data: {
      server_id: string
      name: string
      type: string
      data: Record<string, any>
      description?: string
    }
  ): Promise<Credential> => {
    return request.post<Credential>(`/organizations/${organizationId}/credentials`, data)
  },

  /**
   * Update credential
   */
  update: (
    id: string,
    data: {
      name?: string
      description?: string
      data?: Record<string, any>
    }
  ): Promise<Credential> => {
    return request.put<Credential>(`/credentials/${id}`, data)
  },

  /**
   * Delete credential
   */
  delete: (id: string): Promise<void> => {
    return request.delete<void>(`/credentials/${id}`)
  },

  /**
   * Rotate credential (generate new value)
   */
  rotate: (id: string): Promise<Credential> => {
    return request.post<Credential>(`/credentials/${id}/rotate`)
  },
}

/**
 * OpsPilot Deployments API
 * Deployment management endpoints
 */

import request from '../opspilot/client'
import type { Deployment, DeploymentExecution, DeploymentHistory, PaginatedResponse } from './types'

export const DeploymentsAPI = {
  /**
   * Get all deployments for current organization
   */
  list: (params?: {
    page?: number
    page_size?: number
    server_id?: string
    deployment_type?: string
    status_filter?: string
  }): Promise<PaginatedResponse<Deployment>> => {
    return request.get<PaginatedResponse<Deployment>>('/deployments', { params })
  },

  /**
   * Get deployment by ID
   */
  get: (id: string): Promise<Deployment> => {
    return request.get<Deployment>(`/deployments/${id}`)
  },

  /**
   * Create new deployment configuration
   */
  create: (
    organizationId: string,
    data: {
      server_id: string
      name: string
      description?: string
      deployment_type: 'manual' | 'scheduled' | 'git' | 'docker'
      config: Record<string, any>
      schedule_type?: 'immediate' | 'scheduled'
      schedule_value?: string
    }
  ): Promise<Deployment> => {
    return request.post<Deployment>(`/organizations/${organizationId}/deployments`, data)
  },

  /**
   * Update deployment configuration
   */
  update: (
    id: string,
    data: {
      name?: string
      description?: string
      config?: Record<string, any>
      schedule_type?: 'immediate' | 'scheduled'
      schedule_value?: string
    }
  ): Promise<Deployment> => {
    return request.put<Deployment>(`/deployments/${id}`, data)
  },

  /**
   * Delete deployment configuration
   */
  delete: (id: string): Promise<void> => {
    return request.delete<void>(`/deployments/${id}`)
  },

  /**
   * Execute deployment
   */
  execute: (
    id: string,
    params?: {
      dry_run: boolean
    }
  ): Promise<DeploymentExecution> => {
    return request.post<DeploymentExecution>(`/deployments/${id}/execute`, params)
  },

  /**
   * Rollback deployment to previous version
   */
  rollback: (
    id: string,
    params?: {
      reason?: string
    }
  ): Promise<DeploymentExecution> => {
    return request.post<DeploymentExecution>(`/deployments/${id}/rollback`, params)
  },

  /**
   * Get deployment execution history
   */
  listHistory: (params?: {
    page?: number
    page_size?: number
    server_id?: string
    status_filter?: string
    start_date?: string
    end_date?: string
  }): Promise<PaginatedResponse<DeploymentHistory>> => {
    return request.get<PaginatedResponse<DeploymentHistory>>('/deployment-history', { params })
  },

  /**
   * Get deployment execution by ID
   */
  getExecution: (id: string): Promise<DeploymentHistory> => {
    return request.get<DeploymentHistory>(`/deployment-history/${id}`)
  },
}

/**
 * OpsPilot Organizations API
 * Organization management endpoints
 */

import request from '../opspilot/client'
import type {
  Organization,
  OrganizationMember,
  CreateOrganizationRequest,
  UpdateOrganizationRequest,
  PaginatedResponse,
  CreateServerRequest,
  Server,
} from './types'

export const OrganizationsAPI = {
  /**
   * Get all organizations for current user
   */
  list: (params?: { page?: number; page_size?: number }): Promise<PaginatedResponse<Organization>> => {
    return request.get<PaginatedResponse<Organization>>('/organizations', { params })
  },

  /**
   * Get organization by ID
   */
  get: (id: string): Promise<Organization> => {
    return request.get<Organization>(`/organizations/${id}`)
  },

  /**
   * Get organization by slug
   */
  getBySlug: (slug: string): Promise<Organization> => {
    return request.get<Organization>(`/organizations/by-slug/${slug}`)
  },

  /**
   * Create new organization
   */
  create: (data: CreateOrganizationRequest): Promise<Organization> => {
    return request.post<Organization>('/organizations', data)
  },

  /**
   * Update organization
   */
  update: (id: string, data: UpdateOrganizationRequest): Promise<Organization> => {
    return request.put<Organization>(`/organizations/${id}`, data)
  },

  /**
   * Delete organization
   */
  delete: (id: string): Promise<void> => {
    return request.delete<void>(`/organizations/${id}`)
  },

  /**
   * Get organization members
   */
  listMembers: (
    id: string,
    params?: { page?: number; page_size?: number }
  ): Promise<PaginatedResponse<OrganizationMember>> => {
    return request.get<PaginatedResponse<OrganizationMember>>(`/organizations/${id}/members`, { params })
  },

  /**
   * Add member to organization
   */
  addMember: (
    id: string,
    data: { email: string; role: 'owner' | 'admin' | 'member' | 'viewer' }
  ): Promise<OrganizationMember> => {
    return request.post<OrganizationMember>(`/organizations/${id}/members`, data)
  },

  /**
   * Update member role
   */
  updateMemberRole: (
    id: string,
    memberId: string,
    role: 'owner' | 'admin' | 'member' | 'viewer'
  ): Promise<OrganizationMember> => {
    return request.put<OrganizationMember>(`/organizations/${id}/members/${memberId}`, { role })
  },

  /**
   * Remove member from organization
   */
  removeMember: (id: string, memberId: string): Promise<void> => {
    return request.delete<void>(`/organizations/${id}/members/${memberId}`)
  },

  /**
   * Switch to different organization
   */
  switchOrganization: (id: string): Promise<void> => {
    return request.post<void>(`/organizations/${id}/switch`)
  },

  /**
   * Create a server under an organization
   */
  createServer: (organizationId: string, data: CreateServerRequest): Promise<Server> => {
    return request.post(`/organizations/${organizationId}/servers`, data)
  },
}

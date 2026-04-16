/**
 * OpsPilot API Unified Interface
 * Single unified API object to avoid export conflicts
 */

import request from '../opspilot/client'

/**
 * Unified OpsPilot API
 * All OpsPilot endpoints organized by category
 */
export const OpsPilotAPI = {
  /**
   * Authentication Endpoints
   */
  auth: {
    login: (email: string, password: string) => request.post('/auth/login', { email, password }),

    logout: () => request.post('/auth/logout'),

    register: (data: any) => request.post('/auth/register', data),

    forgotPassword: (email: string) => request.post('/auth/forgot-password', { email }),

    resetPassword: (token: string, newPassword: string) => request.post('/auth/reset-password', { token, newPassword }),
  },

  /**
   * Server Endpoints
   */
  servers: {
    list: (page: number, page_size: number, organization_id: string) =>
      request.get('/servers', { page, page_size, organization_id }),

    getById: (id: string) => request.get(`/servers/${id}`),

    create: (data: any) => request.post('/servers', data),

    update: (id: string, data: any) => request.put(`/servers/${id}`, data),

    delete: (id: string) => request.delete(`/servers/${id}`),

    healthCheck: (id: string) => request.get(`/servers/${id}/health`),
  },

  /**
   * Organization Endpoints
   */
  organizations: {
    list: (page: number, page_size: number) => request.get('/organizations', { page, page_size }),

    getById: (id: string) => request.get(`/organizations/${id}`),

    create: (data: any) => request.post('/organizations', data),

    update: (id: string, data: any) => request.put(`/organizations/${id}`, data),

    delete: (id: string) => request.delete(`/organizations/${id}`),

    listMembers: (id: string, page: number, page_size: number) =>
      request.get(`/organizations/${id}/members`, { page, page_size }),

    addMember: (id: string, data: any) => request.post(`/organizations/${id}/members`, data),

    removeMember: (id: string, memberId: string) => request.delete(`/organizations/${id}/members/${memberId}`),
  },

  /**
   * Alert Endpoints
   */
  alerts: {
    list: (page: number, page_size: number, server_id: string, severity: string, resolved: boolean) =>
      request.get('/alerts', { page, page_size, server_id, severity, resolved }),

    getById: (id: string) => request.get(`/alerts/${id}`),

    create: (data: CreateAlertRequest) => request.post('/alerts', data),

    update: (id: string, data: any) => request.put(`/alerts/${id}`, data),

    dismiss: (id: string) => request.post(`/alerts/${id}/dismiss`),

    getStats: (organization_id: string) => request.get('/alerts/stats', { organization_id }),
  },

  /**
   * Metrics Endpoints
   */
  metrics: {
    getServerMetrics: (server_id: string, start: string, end: string, type: string) =>
      request.get(`/metrics/servers/${server_id}`, { start, end, type }),

    getSystemMetrics: (start: string, end: string, type: string) =>
      request.get('/metrics/system', { start, end, type }),

    getHistorical: (server_id: string, start: string, end: string, type: string) =>
      request.get(`/metrics/servers/${server_id}/historical`, { start, end, type }),
  },

  /**
   * Backup Endpoints
   */
  backups: {
    list: (server_id: string, page: number, page_size: number) =>
      request.get('/backups', { server_id, page, page_size }),

    getById: (id: string) => request.get(`/backups/${id}`),

    create: (data: any) => request.post('/backups', data),

    update: (id: string, data: any) => request.put(`/backups/${id}`, data),

    delete: (id: string) => request.delete(`/backups/${id}`),

    execute: (id: string) => request.post(`/backups/${id}/execute`),

    getReports: (server_id: string, page: number, page_size: number) =>
      request.get('/backups/reports', { server_id, page, page_size }),
  },

  /**
   * Deployment Endpoints
   */
  deployments: {
    list: (server_id: string, page: number, page_size: number) =>
      request.get('/deployments', { server_id, page, page_size }),

    getById: (id: string) => request.get(`/deployments/${id}`),

    create: (data: any) => request.post('/deployments', data),

    update: (id: string, data: any) => request.put(`/deployments/${id}`, data),

    delete: (id: string) => request.delete(`/deployments/${id}`),

    execute: (id: string) => request.post(`/deployments/${id}/execute`),

    getLogs: (id: string, page: number, page_size: number) =>
      request.get(`/deployments/${id}/logs`, { page, page_size }),
  },

  /**
   * SSH Endpoints
   */
  ssh: {
    connect: (server_id: string) => request.post('/ssh/connect', { server_id }),

    disconnect: (server_id: string, session_id: string) => request.post('/ssh/disconnect', { server_id, session_id }),

    sendCommand: (server_id: string, session_id: string, command: string) =>
      request.post('/ssh/send', { server_id, session_id, command }),

    getSessions: (server_id: string) => request.get('/ssh/sessions', { server_id }),
  },

  /**
   * Credentials Endpoints
   */
  credentials: {
    list: (server_id: string, page: number, page_size: number) =>
      request.get('/credentials', { server_id, page, page_size }),

    create: (data: any) => request.post('/credentials', data),

    getById: (id: string) => request.get(`/credentials/${id}`),

    update: (id: string, data: any) => request.put(`/credentials/${id}`, data),

    delete: (id: string) => request.delete(`/credentials/${id}`),
  },

  /**
   * Dashboard Endpoints
   */
  dashboard: {
    getStats: (organization_id: string) => request.get('/dashboard/stats', { organization_id }),

    getServerHealth: (limit: number) => request.get('/dashboard/server-health', { limit }),

    getRecentAlerts: (limit: number) => request.get('/dashboard/recent-alerts', { limit }),
  },
}

// Note: For backward compatibility, you can destructure individual APIs
export const AuthAPI = OpsPilotAPI.auth
export const ServersAPI = OpsPilotAPI.servers
export const OrganizationsAPI = OpsPilotAPI.organizations
export const AlertsAPI = OpsPilotAPI.alerts
export const MetricsAPI = OpsPilotAPI.metrics
export const BackupsAPI = OpsPilotAPI.backups
export const DeploymentsAPI = OpsPilotAPI.deployments
export const SSHAPI = OpsPilotAPI.ssh
export const CredentialsAPI = OpsPilotAPI.credentials
export const DashboardAPI = OpsPilotAPI.dashboard

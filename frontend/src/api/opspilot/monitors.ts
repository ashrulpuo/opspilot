import request from './client'

export interface Monitor {
  id: string
  org_id: string
  server_id?: string
  name: string
  url: string
  type: 'http' | 'https' | 'tcp' | 'dns' | 'push'
  port?: number
  interval_seconds: number
  timeout_seconds: number
  enabled: boolean
  last_status: 'up' | 'down' | 'pending' | 'paused' | null
  last_checked_at: string | null
  consecutive_failures: number
  heartbeat_api_key?: string
  ssl_days_remaining?: number | null
  avg_response_time_ms?: number | null
  uptime_7d?: number | null
  uptime_30d?: number | null
  created_at: string
}

export interface MonitorCheck {
  id: string
  monitor_id: string
  checked_at: string
  status: 'up' | 'down'
  response_time_ms: number | null
  status_code: number | null
  ssl_days_remaining: number | null
  error: string | null
}

export interface MonitorIncident {
  id: string
  monitor_id: string
  started_at: string
  resolved_at: string | null
  duration_seconds: number | null
}

export interface MonitorStats {
  total: number
  up: number
  down: number
  paused: number
  pending: number
}

export interface CreateMonitorRequest {
  name: string
  url: string
  type: 'http' | 'https' | 'tcp' | 'dns' | 'push'
  port?: number
  interval_seconds: number
  timeout_seconds: number
}

export const MonitorsAPI = {
  list: (): Promise<Monitor[]> => request.get('/monitors'),

  get: (id: string): Promise<Monitor> => request.get(`/monitors/${id}`),

  create: (data: CreateMonitorRequest): Promise<Monitor> => request.post('/monitors', data),

  update: (id: string, data: Partial<CreateMonitorRequest> & { enabled?: boolean }): Promise<Monitor> =>
    request.put(`/monitors/${id}`, data),

  delete: (id: string): Promise<void> => request.delete(`/monitors/${id}`),

  getChecks: (id: string, hours = 24): Promise<MonitorCheck[]> =>
    request.get(`/monitors/${id}/checks`, { params: { hours } }),

  getIncidents: (id: string): Promise<MonitorIncident[]> => request.get(`/monitors/${id}/incidents`),

  getStats: (): Promise<MonitorStats> => request.get('/monitors/stats'),
}

/**
 * SaltStack SSE Composable
 *
 * This composable manages SSE (Server-Sent Events) connections
 * for real-time data streaming from the SaltStack backend.
 *
 * Features:
 * - Subscribe to 6 SSE streams (metrics, alerts, services, processes, packages, logs)
 * - JWT authentication with automatic header injection
 * - Auto-reconnect with exponential backoff
 * - Real-time state updates to Pinia stores
 * - Debounce chart updates (500ms)
 * - Proper cleanup on component unmount
 * - Connection status tracking
 */

import { onUnmounted, computed } from 'vue'
import { defineStore } from 'pinia'

import { ServersAPI } from '@/api/opspilot/servers'
import { dashboardPayloadToMetrics } from '@/utils/dashboardMetrics'
import { useOpsPilotAuthStore } from '@/stores/modules/opspilot'

// ============================================
// Types
// ============================================

export interface Metric {
  server_id: string
  metric_name: string
  metric_value: number
  unit: string
  timestamp: string
  metadata?: Record<string, any>
}

export interface Alert {
  id: string
  server_id: string
  alert_type: string
  severity: 'info' | 'warning' | 'critical'
  message: string
  event_data: Record<string, any>
  processed: boolean
  created_at: string
  acknowledged?: boolean
}

export interface ServiceState {
  id: string
  server_id: string
  service_name: string
  status: 'running' | 'stopped' | 'unknown'
  previous_status?: string
  last_checked: string
  status_changed_at?: string
}

export interface Process {
  id: string
  server_id: string
  pid: number
  name: string
  command: string
  username: string
  cpu_percent: number
  memory_percent: number
  state: 'R' | 'S' | 'D' | 'Z' | 'T' | 'W'
  start_time: string
}

export interface Package {
  id: string
  server_id: string
  name: string
  version: string
  architecture: string
  source: string
  is_update_available: boolean
  installed_date: string
  update_version?: string
}

export interface LogEntry {
  id: string
  server_id: string
  timestamp: string
  log_level: 'INFO' | 'WARN' | 'ERROR' | 'DEBUG'
  source: string
  message: string
  metadata?: Record<string, any>
}

export interface SSEMessage {
  type: string // 'metric', 'alert', 'service_state', 'process_list', 'package_update', 'log_entry'
  server_id: string
  user_id?: string
  organization_id?: string
  timestamp: string
  [key: string]: any
}

export interface ConnectionStatus {
  metrics: boolean
  alerts: boolean
  services: boolean
  processes: boolean
  packages: boolean
  logs: boolean
  overall: boolean
}

// ============================================
// Pinia Store Definitions
// ============================================

export const useSaltStore = defineStore('salt', {
  state: () => ({
    /** Salt minion metadata keyed by server id (grains, last_seen, …). Used by SaltInfo tab. */
    minions: {} as Record<string, Record<string, unknown>>,
    metrics: {} as Record<string, Metric>,
    alerts: [] as Alert[],
    services: {} as Record<string, ServiceState>,
    processes: [] as Process[],
    packages: [] as Package[],
    logs: [] as LogEntry[],
    connectionStatus: {
      metrics: false,
      alerts: false,
      services: false,
      processes: false,
      packages: false,
      logs: false,
      overall: false,
    } as ConnectionStatus,
    reconnectAttempts: {} as Record<string, number>,
    lastError: null as string | null,
  }),

  getters: {
    getMetric: state => (serverId: string, metricName: string) => {
      return state.metrics[`${serverId}_${metricName}`]
    },

    getLatestMetrics: state => (serverId: string) => {
      const metrics = Object.values(state.metrics).filter(m => m.server_id === serverId)
      return metrics.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()).slice(-20)
    },

    getLatestAlerts: state => (serverId: string) => {
      return state.alerts.filter(a => a.server_id === serverId).slice(0, 50)
    },

    getServiceState: state => (serverId: string, serviceName: string) => {
      return state.services[`${serverId}_${serviceName}`]
    },

    getProcesses: state => (serverId: string) => {
      return state.processes.filter(p => p.server_id === serverId)
    },

    getPackages: state => (serverId: string) => {
      return state.packages.filter(p => p.server_id === serverId)
    },

    getLogs: state => (serverId: string) => {
      return state.logs.filter(l => l.server_id === serverId)
    },

    getUnreadAlerts: state => {
      return state.alerts.filter(a => !a.acknowledged)
    },

    getPackageUpdateCount: state => (serverId: string) => {
      return state.packages.filter(p => p.server_id === serverId && p.is_update_available).length
    },

    getConnectionStatus: state => {
      return state.connectionStatus
    },

    getOverallConnected: state => {
      const status = state.connectionStatus
      return status.metrics && status.alerts && status.services && status.processes && status.packages && status.logs
    },
  },

  actions: {
    setMetric(metric: Metric) {
      this.metrics[`${metric.server_id}_${metric.metric_name}`] = metric
    },

    addMetric(metric: Metric) {
      this.metrics[`${metric.server_id}_${metric.metric_name}`] = metric
    },

    addAlert(alert: Alert) {
      this.alerts.unshift(alert)
      // Keep only last 1000 alerts
      if (this.alerts.length > 1000) {
        this.alerts = this.alerts.slice(0, 1000)
      }
    },

    acknowledgeAlert(alertId: string) {
      const alert = this.alerts.find(a => a.id === alertId)
      if (alert) {
        alert.acknowledged = true
      }
    },

    setServiceState(serviceState: ServiceState) {
      this.services[`${serviceState.server_id}_${serviceState.service_name}`] = serviceState
    },

    setProcesses(processes: Process[]) {
      this.processes = processes
    },

    addProcess(process: Process) {
      const existingIndex = this.processes.findIndex(p => p.id === process.id)
      if (existingIndex >= 0) {
        this.processes[existingIndex] = process
      } else {
        this.processes.push(process)
      }
      // Keep only last 5000 processes
      if (this.processes.length > 5000) {
        this.processes = this.processes.slice(-5000)
      }
    },

    setPackages(packages: Package[]) {
      this.packages = packages
    },

    addPackage(pkg: Package) {
      const existingIndex = this.packages.findIndex(p => p.id === pkg.id)
      if (existingIndex >= 0) {
        this.packages[existingIndex] = pkg
      } else {
        this.packages.push(pkg)
      }
    },

    setLogs(logs: LogEntry[]) {
      this.logs = logs
    },

    addLog(log: LogEntry) {
      this.logs.unshift(log)
      // Keep only last 1000 logs
      if (this.logs.length > 1000) {
        this.logs = this.logs.slice(0, 1000)
      }
    },

    setConnectionStatus(connectionName: keyof ConnectionStatus, status: boolean) {
      const cs = this.connectionStatus as Record<string, boolean>
      cs[connectionName] = status
      cs.overall = !!(cs.metrics && cs.alerts && cs.services && cs.processes && cs.packages && cs.logs)
    },

    setReconnectAttempt(connectionName: string, attempts: number) {
      ;(this.reconnectAttempts as Record<string, number>)[connectionName] = attempts
    },

    incrementReconnectAttempt(connectionName: string) {
      const m = this.reconnectAttempts as Record<string, number>
      m[connectionName] = (m[connectionName] || 0) + 1
    },

    resetReconnectAttempts(connectionName: string) {
      ;(this.reconnectAttempts as Record<string, number>)[connectionName] = 0
    },

    setError(error: string | null) {
      this.lastError = error
    },

    clearAlerts() {
      this.alerts = []
    },

    clearLogs() {
      this.logs = []
    },

    clearProcesses() {
      this.processes = []
    },
  },
})

// Type for Pinia store
type SaltStore = ReturnType<typeof useSaltStore>

// ============================================
// Helper Functions
// ============================================

/**
 * Access token from auth store (persisted under localStorage key `opspilot-auth`).
 */
const getJWTToken = (): string | null => {
  try {
    const auth = useOpsPilotAuthStore()
    const token = auth.accessToken
    return typeof token === 'string' && token.length > 0 ? token : null
  } catch {
    return null
  }
}

/**
 * Build SSE URL with server filter and JWT (native EventSource cannot send Authorization header).
 */
const buildSSEUrl = (baseUrl: string, endpoint: string, serverId?: string, accessToken?: string | null): string => {
  const params = new URLSearchParams()
  if (serverId) {
    params.set('server_id', serverId)
  }
  if (accessToken) {
    params.set('access_token', accessToken)
  }
  const qs = params.toString()
  const path = `${baseUrl}/${endpoint}`
  return qs ? `${path}?${qs}` : path
}

/**
 * Parse SSE message
 */
const parseSSEMessage = (event: MessageEvent): SSEMessage | null => {
  try {
    // Check if it's an event (with event type) or just data
    if (event.type) {
      return JSON.parse(event.data) as SSEMessage
    } else {
      return JSON.parse(event.data) as SSEMessage
    }
  } catch (error) {
    console.error('Failed to parse SSE message:', error, event.data)
    return null
  }
}

/**
 * Debounce function for chart updates
 */
const debounce = <T extends (...args: any[]) => any>(func: T, wait: number): ((...args: any[]) => void) => {
  let timeout: ReturnType<typeof setTimeout> | null = null

  return function (this: any, ...args: any[]) {
    const context = this
    if (timeout !== null) clearTimeout(timeout)
    timeout = setTimeout(() => {
      func.apply(context, args)
    }, wait)
  }
}

/**
 * Format timestamp for display
 */
const formatTimestamp = (timestamp: string): string => {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()

  if (diffMs < 60000) {
    // Less than 1 minute
    return 'Just now'
  } else if (diffMs < 3600000) {
    // Less than 1 hour
    const minutes = Math.floor(diffMs / 60000)
    return `${minutes}m ago`
  } else if (diffMs < 86400000) {
    // Less than 1 day
    const hours = Math.floor(diffMs / 3600000)
    return `${hours}h ago`
  } else {
    const days = Math.floor(diffMs / 86400000)
    return `${days}d ago`
  }
}

/**
 * Get alert color class based on severity
 */
const getAlertColorClass = (severity: string): string => {
  switch (severity) {
    case 'critical':
      return 'text-red-600'
    case 'warning':
      return 'text-yellow-600'
    case 'info':
    default:
      return 'text-blue-600'
  }
}

/**
 * Get alert background class based on severity
 */
const getAlertBgClass = (severity: string): string => {
  switch (severity) {
    case 'critical':
      return 'bg-red-50'
    case 'warning':
      return 'bg-yellow-50'
    case 'info':
    default:
      return 'bg-blue-50'
  }
}

// ============================================
// Shared SSE pool (one set of EventSources per server)
// ============================================
// Many server-detail components call useSaltStream() for the same serverId. Each
// call used to run connectAll() → duplicate EventSources and a request storm.

const SSE_STREAM_KEYS = ['metrics', 'alerts', 'services', 'processes', 'packages', 'logs'] as const
export type SaltStreamKey = (typeof SSE_STREAM_KEYS)[number]

type SaltStreamPool = {
  refCount: number
  eventSources: Record<SaltStreamKey, EventSource | null>
  /** Per-stream manual reconnect timers (must not stack with browser EventSource auto-retry). */
  reconnectTimers: Partial<Record<SaltStreamKey, ReturnType<typeof setTimeout>>>
}

const saltStreamPools = new Map<string, SaltStreamPool>()

function clearReconnectTimer(pool: SaltStreamPool, streamName: SaltStreamKey): void {
  const t = pool.reconnectTimers[streamName]
  if (t !== undefined) {
    clearTimeout(t)
    delete pool.reconnectTimers[streamName]
  }
}

function clearAllReconnectTimers(pool: SaltStreamPool): void {
  for (const key of SSE_STREAM_KEYS) {
    clearReconnectTimer(pool, key)
  }
}

function acquireSaltStreamPool(serverId: string): SaltStreamPool {
  let pool = saltStreamPools.get(serverId)
  if (!pool) {
    pool = {
      refCount: 0,
      eventSources: {
        metrics: null,
        alerts: null,
        services: null,
        processes: null,
        packages: null,
        logs: null,
      },
      reconnectTimers: {},
    }
    saltStreamPools.set(serverId, pool)
  }
  pool.refCount++
  return pool
}

function emptyPoolEventSources(pool: SaltStreamPool): void {
  pool.eventSources.metrics = null
  pool.eventSources.alerts = null
  pool.eventSources.services = null
  pool.eventSources.processes = null
  pool.eventSources.packages = null
  pool.eventSources.logs = null
}

function closePoolStreams(pool: SaltStreamPool, store: SaltStore): void {
  clearAllReconnectTimers(pool)
  for (const name of SSE_STREAM_KEYS) {
    const es = pool.eventSources[name]
    if (es) {
      es.close()
      store.setConnectionStatus(name as keyof ConnectionStatus, false)
      pool.eventSources[name] = null
    }
  }
}

function releaseSaltStreamPool(serverId: string, store: SaltStore): void {
  const pool = saltStreamPools.get(serverId)
  if (!pool) {
    return
  }
  pool.refCount--
  if (pool.refCount > 0) {
    return
  }
  closePoolStreams(pool, store)
  saltStreamPools.delete(serverId)
}

async function hydrateDashboardMetrics(serverId: string, store: SaltStore): Promise<void> {
  try {
    const res = await ServersAPI.collectMetrics(serverId)
    const payload = res.metrics as Record<string, unknown>
    const rows = dashboardPayloadToMetrics(serverId, payload)
    for (const row of rows) {
      store.addMetric(row as Metric)
    }
  } catch (e) {
    console.warn('[useSaltStream] hydrate metrics failed', serverId, e)
  }
}

function _procStateChar(raw: string | undefined): Process['state'] {
  const c = (raw || 'S').trim()[0]?.toUpperCase() ?? 'S'
  return (['R', 'S', 'D', 'Z', 'T', 'W'].includes(c) ? c : 'S') as Process['state']
}

async function hydrateAgentSnapshot(serverId: string, store: SaltStore): Promise<void> {
  try {
    const [svcRows, procRows] = await Promise.all([
      ServersAPI.getSaltServices(serverId),
      ServersAPI.getSaltProcesses(serverId),
    ])
    for (const s of svcRows) {
      store.setServiceState({
        id: s.id,
        server_id: s.server_id,
        service_name: s.service_name,
        status: (['running', 'stopped', 'unknown'].includes(s.status) ? s.status : 'unknown') as ServiceState['status'],
        previous_status: s.previous_status ?? undefined,
        last_checked: s.last_checked,
      })
    }

    const mapped: Process[] = procRows.map(
      (p): Process => ({
        id: p.id,
        server_id: p.server_id,
        pid: p.pid,
        name: p.name,
        command: p.command ?? '',
        username: p.username ?? '',
        cpu_percent: p.cpu_percent ?? 0,
        memory_percent: p.memory_percent ?? 0,
        state: _procStateChar(p.state),
        start_time: p.start_time ?? new Date().toISOString(),
      })
    )
    const rest = store.processes.filter(pr => pr.server_id !== serverId)
    store.setProcesses([...rest, ...mapped])
  } catch (e) {
    console.warn('[useSaltStream] hydrate agent snapshot failed', serverId, e)
  }
}

// ============================================
// Main Composable
// ============================================

export function useSaltStream(serverId: string) {
  // Pinia store
  const store = useSaltStore()
  const {
    addMetric,
    addAlert,
    setServiceState,
    addProcess,
    addPackage,
    addLog,
    setConnectionStatus,
    incrementReconnectAttempt,
    resetReconnectAttempts,
    setError,
  } = store

  const pool = acquireSaltStreamPool(serverId)

  const metrics = computed(() => {
    const prefix = `${serverId}_`
    const out: Record<string, Metric> = {}
    for (const [key, m] of Object.entries(store.metrics)) {
      if (key.startsWith(prefix)) {
        out[m.metric_name] = m
      }
    }
    return out
  })

  // Reconnection settings
  const MAX_RECONNECT_ATTEMPTS = 5
  const RECONNECT_DELAY_BASE = 5000 // 5s base
  const RECONNECT_DELAY_MAX = 60000 // 1min max

  const debouncedChartUpdate = (_metric: Metric) => {}

  // Connect to SSE stream
  const connectToStream = (streamName: SaltStreamKey, endpoint: string) => {
    const token = getJWTToken()
    if (!token) {
      console.error(`No JWT token available for ${streamName}`)
      store.setError(`No JWT token available for ${streamName}`)
      return
    }

    try {
      clearReconnectTimer(pool, streamName)

      const existing = pool.eventSources[streamName]
      if (existing) {
        // Drop ref before close() so onerror on the old socket is ignored (no duplicate retries).
        pool.eventSources[streamName] = null
        existing.close()
      }

      const url = buildSSEUrl('/api/v1/stream', endpoint, serverId, token)
      const es = new EventSource(url, {
        withCredentials: true,
      })

      es.onopen = () => {
        // stream opened
        clearReconnectTimer(pool, streamName)
        store.setConnectionStatus(streamName, true)
        store.resetReconnectAttempts(streamName)
        store.setError(null)
      }

      es.onmessage = (event: MessageEvent) => {
        const message = parseSSEMessage(event)
        if (!message) {
          return
        }

        // Only mutate store when status actually changes (avoids re-renders on every message)
        if (!(store.connectionStatus as Record<string, boolean>)[streamName]) {
          store.setConnectionStatus(streamName, true)
        }

        // Handle different message types
        switch (message.type) {
          case 'metric':
            store.addMetric(message as Metric)
            break
          case 'alert':
            store.addAlert(message as Alert)
            // Show notification for critical alerts
            const alert = message as Alert
            if (alert.severity === 'critical') {
              showNotification(alert.message, alert.alert_type, alert.severity)
            }
            break
          case 'service_state':
            store.setServiceState(message as ServiceState)
            break
          case 'process_list':
            store.addProcess(message as Process)
            break
          case 'package_update':
            store.addPackage(message as Package)
            break
          case 'log_entry':
            store.addLog(message as LogEntry)
            break
        }
      }

      es.onerror = () => {
        // Ignore callbacks from a connection we already replaced (new EventSource assigned).
        if (pool.eventSources[streamName] !== es) {
          return
        }

        console.error(`SSE stream error: ${streamName}`)
        pool.eventSources[streamName] = null
        // Stop the browser's built-in EventSource reconnect loop (we reconnect manually below).
        es.close()

        store.setConnectionStatus(streamName, false)
        store.incrementReconnectAttempt(streamName)
        store.setError(`SSE connection error: ${streamName}`)

        const attempts = (store.reconnectAttempts as Record<string, number>)[streamName] ?? 0
        if (attempts >= MAX_RECONNECT_ATTEMPTS) {
          console.error(`Max reconnection attempts reached for ${streamName}`)
          store.setError(`Max reconnection attempts reached for ${streamName}`)
          return
        }

        clearReconnectTimer(pool, streamName)

        const delay = Math.min(RECONNECT_DELAY_BASE * Math.pow(2, attempts), RECONNECT_DELAY_MAX)
        // reconnecting

        pool.reconnectTimers[streamName] = setTimeout(() => {
          delete pool.reconnectTimers[streamName]
          if (!saltStreamPools.has(serverId)) {
            return
          }
          connectToStream(streamName, endpoint)
        }, delay)
      }

      pool.eventSources[streamName] = es
    } catch (error) {
      console.error(`Failed to create SSE connection for ${streamName}:`, error)
      store.setConnectionStatus(streamName, false)
      store.setError(`Failed to create SSE connection for ${streamName}`)
    }
  }

  // Connect to all streams
  const connectAll = () => {
    // connecting

    connectToStream('metrics', 'metrics')
    connectToStream('alerts', 'alerts')
    connectToStream('services', 'services')
    connectToStream('processes', 'processes')
    connectToStream('packages', 'packages')
    connectToStream('logs', 'logs')
  }

  /** Drop one subscriber; closes streams only when last component for this server unmounts. */
  const disconnectAll = () => {
    releaseSaltStreamPool(serverId, store)
  }

  /** Close sockets without releasing subscription count (manual reconnect). */
  const forceCloseAllStreams = () => {
    closePoolStreams(pool, store)
    emptyPoolEventSources(pool)
  }

  // Show browser notification for critical alerts
  const showNotification = (message: string, type: string, severity: string) => {
    if ('Notification' in window) {
      const options = {
        body: message,
        icon: severity === 'critical' ? '/critical-icon.png' : '/warning-icon.png',
        badge: severity === 'critical' ? '!' : '⚠',
        tag: 'opspilot-alert',
        requireInteraction: true,
      }

      new Notification(`OpsPilot Alert: ${type}`, options)
    }
  }

  // First subscriber for this server opens the shared SSE bundle
  if (pool.refCount === 1) {
    connectAll()
    void Promise.all([hydrateDashboardMetrics(serverId, store), hydrateAgentSnapshot(serverId, store)])
  }

  // Cleanup on unmount
  onUnmounted(() => {
    disconnectAll()
  })

  // Return reactive state and actions
  return {
    // Connection status
    connectionStatus: computed(() => store.getConnectionStatus),
    overallConnected: computed(() => store.getOverallConnected),
    isConnected: computed(() => store.connectionStatus.metrics),
    lastError: computed(() => store.lastError),

    // Metrics
    metrics,
    getMetric: (metricName: string) => store.getMetric(serverId, metricName),
    getLatestMetrics: () => store.getLatestMetrics(serverId),

    // Alerts
    alerts: computed(() => store.alerts),
    getLatestAlerts: () => store.getLatestAlerts(serverId),
    acknowledgeAlert: (alertId: string) => store.acknowledgeAlert(alertId),
    unreadAlerts: computed(() => store.getUnreadAlerts),
    clearAlerts: () => store.clearAlerts(),

    // Services (full map — components filter by server_id)
    services: computed(() => store.services),
    /** Alias for legacy / parent views */
    serviceStates: computed(() => store.services),

    getServiceState: (serviceName: string) => store.getServiceState(serverId, serviceName),

    // Processes
    processes: computed(() => store.processes),
    getProcesses: () => store.getProcesses(serverId),

    // Packages
    packages: computed(() => store.packages),
    getPackages: () => store.getPackages(serverId),
    packageUpdateCount: computed(() => store.getPackageUpdateCount(serverId)),

    // Logs
    logs: computed(() => store.logs),
    getLogs: () => store.getLogs(serverId),

    // Actions
    reconnect: () => {
      // reconnecting all streams
      forceCloseAllStreams()
      connectAll()
      void Promise.all([hydrateDashboardMetrics(serverId, store), hydrateAgentSnapshot(serverId, store)])
    },

    disconnect: disconnectAll,
    disconnectAll,
    hydrateDashboardMetrics: () => hydrateDashboardMetrics(serverId, store),
    hydrateAgentSnapshot: () => hydrateAgentSnapshot(serverId, store),

    // Alert helpers
    getAlertColorClass,
    getAlertBgClass,
    formatTimestamp,
    debouncedChartUpdate,
  }
}

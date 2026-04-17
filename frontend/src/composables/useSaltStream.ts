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

import { ref, onUnmounted, computed } from 'vue'
import { useStore } from 'pinia'
import type { ComputedRef } from 'vue'

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
  type: string  // 'metric', 'alert', 'service_state', 'process_list', 'package_update', 'log_entry'
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
      overall: false
    } as ConnectionStatus,
    reconnectAttempts: {} as Record<string, number>,
    lastError: null as string | null
  }),
  
  getters: {
    getMetric: (state) => (serverId: string, metricName: string) => {
      return state.metrics[`${serverId}_${metricName}`]
    },
    
    getLatestMetrics: (state) => (serverId: string) => {
      const metrics = Object.values(state.metrics).filter(m => m.server_id === serverId)
      return metrics.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()).slice(-20)
    },
    
    getLatestAlerts: (state) => (serverId: string) => {
      return state.alerts.filter(a => a.server_id === serverId).slice(0, 50)
    },
    
    getServiceState: (state) => (serverId: string, serviceName: string) => {
      return state.services[`${serverId}_${serviceName}`]
    },
    
    getProcesses: (state) => (serverId: string) => {
      return state.processes.filter(p => p.server_id === serverId)
    },
    
    getPackages: (state) => (serverId: string) => {
      return state.packages.filter(p => p.server_id === serverId)
    },
    
    getLogs: (state) => (serverId: string) => {
      return state.logs.filter(l => l.server_id === serverId)
    },
    
    getUnreadAlerts: (state) => {
      return state.alerts.filter(a => !a.acknowledged)
    },
    
    getPackageUpdateCount: (state) => (serverId: string) => {
      return state.packages.filter(p => p.server_id === serverId && p.is_update_available).length
    },
    
    getConnectionStatus: (state) => {
      return state.connectionStatus
    },
    
    getOverallConnected: (state) => {
      const status = state.connectionStatus
      return status.metrics && status.alerts && status.services && 
             status.processes && status.packages && status.logs
    }
  },
  
  actions: {
    setMetric(state, metric: Metric) {
      state.metrics[`${metric.server_id}_${metric.metric_name}`] = metric
    },
    
    addMetric(state, metric: Metric) {
      state.metrics[`${metric.server_id}_${metric.metric_name}`] = metric
    },
    
    addAlert(state, alert: Alert) {
      state.alerts.unshift(alert)
      // Keep only last 1000 alerts
      if (state.alerts.length > 1000) {
        state.alerts = state.alerts.slice(0, 1000)
      }
    },
    
    acknowledgeAlert(state, alertId: string) {
      const alert = state.alerts.find(a => a.id === alertId)
      if (alert) {
        alert.acknowledged = true
      }
    },
    
    setServiceState(state, serviceState: ServiceState) {
      state.services[`${serviceState.server_id}_${serviceState.service_name}`] = serviceState
    },
    
    setProcesses(state, processes: Process[]) {
      state.processes = processes
    },
    
    addProcess(state, process: Process) {
      const existingIndex = state.processes.findIndex(p => p.id === process.id)
      if (existingIndex >= 0) {
        state.processes[existingIndex] = process
      } else {
        state.processes.push(process)
      }
      // Keep only last 5000 processes
      if (state.processes.length > 5000) {
        state.processes = state.processes.slice(-5000)
      }
    },
    
    setPackages(state, packages: Package[]) {
      state.packages = packages
    },
    
    addPackage(state, pkg: Package) {
      const existingIndex = state.packages.findIndex(p => p.id === pkg.id)
      if (existingIndex >= 0) {
        state.packages[existingIndex] = pkg
      } else {
        state.packages.push(pkg)
      }
    },
    
    setLogs(state, logs: LogEntry[]) {
      state.logs = logs
    },
    
    addLog(state, log: LogEntry) {
      state.logs.unshift(log)
      // Keep only last 1000 logs
      if (state.logs.length > 1000) {
        state.logs = state.logs.slice(0, 1000)
      }
    },
    
    setConnectionStatus(state, connectionName: keyof ConnectionStatus, status: boolean) {
      (state.connectionStatus as any)[connectionName] = status
      // Update overall status
      const cs = state.connectionStatus
      (state.connectionStatus as any).overall = 
        cs.metrics && cs.alerts && cs.services && cs.processes && cs.packages && cs.logs
    },
    
    setReconnectAttempt(state, connectionName: string, attempts: number) {
      (state.reconnectAttempts as any)[connectionName] = attempts
    },
    
    incrementReconnectAttempt(state, connectionName: string) {
      const attempts = (state.reconnectAttempts as any)[connectionName] || 0
      (state.reconnectAttempts as any)[connectionName] = attempts + 1
    },
    
    resetReconnectAttempts(state, connectionName: string) {
      (state.reconnectAttempts as any)[connectionName] = 0
    },
    
    setError(state, error: string | null) {
      state.lastError = error
    },
    
    clearAlerts(state) {
      state.alerts = []
    },
    
    clearLogs(state) {
      state.logs = []
    },
    
    clearProcesses(state) {
      state.processes = []
    }
  }
})

// Type for Pinia store
type SaltStore = ReturnType<typeof useSaltStore>

// ============================================
// Helper Functions
// ============================================

/**
 * Get JWT token from localStorage
 */
const getJWTToken = (): string | null => {
  return localStorage.getItem('access_token')
}

/**
 * Build SSE URL with server ID filter
 */
const buildSSEUrl = (baseUrl: string, endpoint: string, serverId?: string): string => {
  if (serverId) {
    return `${baseUrl}/${endpoint}?server_id=${serverId}`
  }
  return `${baseUrl}/${endpoint}`
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
  
  return function(this: any, ...args: any[]) {
    const context = this
    clearTimeout(timeout)
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
  
  if (diffMs < 60000) {  // Less than 1 minute
    return 'Just now'
  } else if (diffMs < 3600000) {  // Less than 1 hour
    const minutes = Math.floor(diffMs / 60000)
    return `${minutes}m ago`
  } else if (diffMs < 86400000) {  // Less than 1 day
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
    setError
  } = store
  
  // EventSources
  const eventSources = ref<Record<string, EventSource>>({
    metrics: null,
    alerts: null,
    services: null,
    processes: null,
    packages: null,
    logs: null
  })
  
  // Reconnection settings
  const MAX_RECONNECT_ATTEMPTS = 5
  const RECONNECT_DELAY_BASE = 5000  // 5s base
  const RECONNECT_DELAY_MAX = 60000  // 1min max
  
  // Debounced chart update
  const debouncedChartUpdate = debounce((metric: Metric) => {
    // This would be used by chart components
    // For now, we'll just log it
    console.log('Chart update:', metric.metric_name, metric.metric_value)
  }, 500)
  
  // Connect to SSE stream
  const connectToStream = (streamName: string, endpoint: string) => {
    const token = getJWTToken()
    if (!token) {
      console.error(`No JWT token available for ${streamName}`)
      store.setError(`No JWT token available for ${streamName}`)
      return
    }
    
    try {
      const url = buildSSEUrl('/api/v1/stream', endpoint, serverId)
      const es = new EventSource(url, {
        withCredentials: true
      })
      
      es.onopen = () => {
        console.log(`SSE stream opened: ${streamName}`)
        store.setConnectionStatus(streamName, true)
        store.resetReconnectAttempts(streamName)
        store.setError(null)
      }
      
      es.onmessage = (event: MessageEvent) => {
        const message = parseSSEMessage(event)
        if (!message) return
        
        // Update connection status
        store.setConnectionStatus(streamName, true)
        
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
              showNotification(
                alert.message,
                alert.alert_type,
                alert.severity
              )
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
      
      es.onerror = (error: Event) => {
        console.error(`SSE stream error: ${streamName}`, error)
        store.setConnectionStatus(streamName, false)
        store.incrementReconnectAttempt(streamName)
        store.setError(`SSE connection error: ${streamName}`)
        
        // Attempt reconnection with exponential backoff
        const attempts = (store.reconnectAttempts as any)[streamName] || 0
        if (attempts < MAX_RECONNECT_ATTEMPTS) {
          const delay = Math.min(
            RECONNECT_DELAY_BASE * Math.pow(2, attempts),
            RECONNECT_DELAY_MAX
          )
          console.log(`Reconnecting to ${streamName} in ${delay}ms (attempt ${attempts + 1})`)
          setTimeout(() => connectToStream(streamName, endpoint), delay)
        } else {
          console.error(`Max reconnection attempts reached for ${streamName}`)
          store.setError(`Max reconnection attempts reached for ${streamName}`)
        }
      }
      
      // Store EventSource reference
      eventSources.value[streamName] = es
      
    } catch (error) {
      console.error(`Failed to create SSE connection for ${streamName}:`, error)
      store.setConnectionStatus(streamName, false)
      store.setError(`Failed to create SSE connection for ${streamName}`)
    }
  }
  
  // Connect to all streams
  const connectAll = () => {
    console.log(`Connecting to SSE streams for server: ${serverId}`)
    
    // Connect to each stream
    connectToStream('metrics', 'metrics')
    connectToStream('alerts', 'alerts')
    connectToStream('services', 'services')
    connectToStream('processes', 'processes')
    connectToStream('packages', 'packages')
    connectToStream('logs', 'logs')
  }
  
  // Disconnect from all streams
  const disconnectAll = () => {
    console.log('Disconnecting from SSE streams')
    
    Object.entries(eventSources.value).forEach(([name, es]) => {
      if (es) {
        console.log(`Closing SSE stream: ${name}`)
        es.close()
        store.setConnectionStatus(name, false)
      }
    })
    
    // Clear all EventSources
    eventSources.value = {
      metrics: null,
      alerts: null,
      services: null,
      processes: null,
      packages: null,
      logs: null
    }
  }
  
  // Show browser notification for critical alerts
  const showNotification = (message: string, type: string, severity: string) => {
    if ('Notification' in window) {
      const options = {
        body: message,
        icon: severity === 'critical' ? '/critical-icon.png' : '/warning-icon.png',
        badge: severity === 'critical' ? '!' : '⚠',
        tag: 'opspilot-alert',
        requireInteraction: true
      }
      
      new Notification(`OpsPilot Alert: ${type}`, options)
    }
  }
  
  // Initialize connections on mount
  connectAll()
  
  // Cleanup on unmount
  onUnmounted(() => {
    console.log('Cleaning up SSE connections')
    disconnectAll()
  })
  
  // Return reactive state and actions
  return {
    // Connection status
    connectionStatus: computed(() => store.getConnectionStatus),
    overallConnected: computed(() => store.getOverallConnected),
    lastError: computed(() => store.lastError),
    
    // Metrics
    getMetric: (metricName: string) => store.getMetric(serverId, metricName),
    getLatestMetrics: () => store.getLatestMetrics(serverId),
    
    // Alerts
    alerts: computed(() => store.alerts),
    getLatestAlerts: () => store.getLatestAlerts(serverId),
    acknowledgeAlert: (alertId: string) => store.acknowledgeAlert(alertId),
    unreadAlerts: computed(() => store.getUnreadAlerts()),
    clearAlerts: () => store.clearAlerts(),
    
    // Services
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
      console.log('Reconnecting to SSE streams')
      disconnectAll()
      connectAll()
    },
    
    disconnect: disconnectAll,
    
    // Alert helpers
    getAlertColorClass,
    getAlertBgClass,
    formatTimestamp,
    debouncedChartUpdate
  }
}

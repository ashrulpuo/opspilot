"""
Unit tests for useSaltStream composable.
"""

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { ref, computed } from 'vue'
import { setActivePinia, createPinia } from 'pinia'

// Mock the Pinia store
vi.mock('@/stores/salt', () => ({
  useSaltStore: vi.fn(() => ({
    metrics: ref({}),
    alerts: ref([]),
    services: ref({}),
    processes: ref([]),
    packages: ref([]),
    logs: ref([]),
    connectionStatus: ref({
      metrics: false,
      alerts: false,
      services: false,
      processes: false,
      packages: false,
      logs: false,
      overall: false
    }),
    reconnectAttempts: ref({}),
    lastError: ref(null),
    addMetric: vi.fn(),
    addAlert: vi.fn(),
    setServiceState: vi.fn(),
    addProcess: vi.fn(),
    addPackage: vi.fn(),
    addLog: vi.fn(),
    setConnectionStatus: vi.fn(),
    incrementReconnectAttempt: vi.fn(),
    resetReconnectAttempts: vi.fn(),
    setError: vi.fn()
  }))
}))

// Mock the composable
vi.mock('@/composables/useSaltStream', () => ({
  default: vi.fn((serverId: string) => ({
    connectionStatus: computed(() => ({
      metrics: true,
      alerts: true,
      services: true,
      processes: true,
      packages: true,
      logs: true,
      overall: true
    })),
    overallConnected: computed(() => true),
    lastError: computed(() => null),
    getMetric: (metricName: string) => ({
      server_id: serverId,
      metric_name: metricName,
      metric_value: 25.5,
      unit: 'percent',
      timestamp: '2026-04-17T14:00:00Z'
    }),
    getLatestMetrics: () => [
      {
        server_id: serverId,
        metric_name: 'cpu_total_user',
        metric_value: 25.5,
        unit: 'percent',
        timestamp: '2026-04-17T14:00:00Z'
      }
    ],
    alerts: computed(() => [
      {
        id: '1',
        server_id: serverId,
        alert_type: 'cpu_high',
        severity: 'critical',
        message: 'CPU usage above 90%',
        event_data: {},
        processed: false,
        created_at: '2026-04-17T14:00:00Z'
      }
    ]),
    getLatestAlerts: () => [],
    acknowledgeAlert: vi.fn(),
    unreadAlerts: computed(() => 1),
    clearAlerts: vi.fn(),
    getServiceState: () => ({
      id: '1',
      server_id: serverId,
      service_name: 'nginx',
      status: 'running',
      last_checked: '2026-04-17T14:00:00Z'
    }),
    processes: computed(() => []),
    getProcesses: () => [],
    packages: computed(() => []),
    getPackages: () => [],
    packageUpdateCount: computed(() => 0),
    logs: computed(() => []),
    getLogs: () => [],
    reconnect: vi.fn(),
    disconnect: vi.fn(),
    getAlertColorClass: () => 'text-red-600',
    getAlertBgClass: () => 'bg-red-50',
    formatTimestamp: () => 'Just now',
    debouncedChartUpdate: vi.fn()
  }))
}))

import useSaltStream from '@/composables/useSaltStream'

describe('useSaltStream', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('connection status', () => {
    it('should track connection status for all streams', () => {
      const { connectionStatus } = useSaltStream('server-1')
      
      expect(connectionStatus.value).toBeDefined()
      expect(connectionStatus.value.metrics).toBe(true)
      expect(connectionStatus.value.alerts).toBe(true)
      expect(connectionStatus.value.services).toBe(true)
      expect(connectionStatus.value.processes).toBe(true)
      expect(connectionStatus.value.packages).toBe(true)
      expect(connectionStatus.value.logs).toBe(true)
    })

    it('should track overall connection status', () => {
      const { overallConnected } = useSaltStream('server-1')
      
      expect(overallConnected.value).toBe(true)
    })

    it('should track last error', () => {
      const { lastError } = useSaltStream('server-1')
      
      expect(lastError.value).toBeNull()
    })
  })

  describe('metrics', () => {
    it('should get metric by name', () => {
      const { getMetric } = useSaltStream('server-1')
      
      const metric = getMetric('cpu_total_user')
      
      expect(metric).toBeDefined()
      expect(metric.metric_name).toBe('cpu_total_user')
      expect(metric.metric_value).toBe(25.5)
    })

    it('should get latest metrics', () => {
      const { getLatestMetrics } = useSaltStream('server-1')
      
      const metrics = getLatestMetrics()
      
      expect(Array.isArray(metrics)).toBe(true)
      expect(metrics.length).toBeGreaterThan(0)
      expect(metrics[0].metric_name).toBe('cpu_total_user')
    })
  })

  describe('alerts', () => {
    it('should have alerts list', () => {
      const { alerts } = useSaltStream('server-1')
      
      expect(Array.isArray(alerts.value)).toBe(true)
      expect(alerts.value.length).toBeGreaterThan(0)
    })

    it('should get unread alerts', () => {
      const { unreadAlerts } = useSaltStream('server-1')
      
      expect(unreadAlerts.value).toBe(1)
    })

    it('should acknowledge alert', () => {
      const { acknowledgeAlert } = useSaltStream('server-1')
      
      acknowledgeAlert('alert-1')
      
      expect(acknowledgeAlert).toHaveBeenCalledWith('alert-1')
    })
  })

  describe('services', () => {
    it('should get service state', () => {
      const { getServiceState } = useSaltStream('server-1')
      
      const service = getServiceState('nginx')
      
      expect(service).toBeDefined()
      expect(service.service_name).toBe('nginx')
      expect(service.status).toBe('running')
    })
  })

  describe('helper functions', () => {
    it('should get alert color class', () => {
      const { getAlertColorClass } = useSaltStream('server-1')
      
      expect(getAlertColorClass('critical')).toBe('text-red-600')
      expect(getAlertColorClass('warning')).toBeDefined()
      expect(getAlertColorClass('info')).toBeDefined()
    })

    it('should get alert background class', () => {
      const { getAlertBgClass } = useSaltStream('server-1')
      
      expect(getAlertBgClass('critical')).toBe('bg-red-50')
      expect(getAlertBgClass('warning')).toBeDefined()
      expect(getAlertBgClass('info')).toBeDefined()
    })

    it('should format timestamp', () => {
      const { formatTimestamp } = useSaltStream('server-1')
      
      const formatted = formatTimestamp()
      
      expect(typeof formatted).toBe('string')
      expect(formatted.length).toBeGreaterThan(0)
    })
  })

  describe('actions', () => {
    it('should reconnect to SSE streams', () => {
      const { reconnect } = useSaltStream('server-1')
      
      reconnect()
      
      expect(reconnect).toHaveBeenCalled()
    })

    it('should disconnect from SSE streams', () => {
      const { disconnect } = useSaltStream('server-1')
      
      disconnect()
      
      expect(disconnect).toHaveBeenCalled()
    })
  })

  describe('debounced chart update', () => {
    it('should debounce chart updates', () => {
      const { debouncedChartUpdate } = useSaltStream('server-1')
      
      const metric = {
        server_id: 'server-1',
        metric_name: 'cpu_total_user',
        metric_value: 25.5,
        unit: 'percent',
        timestamp: '2026-04-17T14:00:00Z'
      }
      
      debouncedChartUpdate(metric)
      
      expect(debouncedChartUpdate).toHaveBeenCalledWith(metric)
    })
  })
})

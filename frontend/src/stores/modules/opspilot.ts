/**
 * OpsPilot Stores
 * Pinia stores for OpsPilot application state
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import piniaPersistConfig from '@/stores/helper/persist'
import { AuthAPI } from '@/api/opspilot/auth'
import type { User, LoginRequest, RegisterRequest, BootstrapRequest } from '@/api/opspilot/types'

// ============================================
// Auth Store
// ============================================

export const useOpsPilotAuthStore = defineStore(
  'opspilot-auth',
  () => {
    const accessToken = ref<string>('')
    const refreshToken = ref<string>('')
    const user = ref<User | null>(null)
    const isAuthenticated = ref<boolean>(false)
    /** null = not yet loaded from API */
    const setupRequired = ref<boolean | null>(null)

    const isAuth = computed(() => isAuthenticated.value && !!accessToken.value)

    const setAuth = (token: string, refresh: string, userData: User) => {
      accessToken.value = token
      refreshToken.value = refresh
      user.value = userData
      isAuthenticated.value = true
    }

    const clearAuth = () => {
      accessToken.value = ''
      refreshToken.value = ''
      user.value = null
      isAuthenticated.value = false
      setupRequired.value = null
    }

    const updateToken = (token: string) => {
      accessToken.value = token
    }

    const updateUser = (userData: Partial<User>) => {
      if (user.value) {
        user.value = { ...user.value, ...userData }
      }
    }

    const login = async (credentials: LoginRequest) => {
      const response = await AuthAPI.login(credentials)
      // Set token first so getCurrentUser() has auth
      accessToken.value = response.access_token
      refreshToken.value = response.refresh_token ?? ''
      isAuthenticated.value = true
      // Now get user info with the token
      try {
        const userInfo = await AuthAPI.getCurrentUser()
        user.value = userInfo
      } catch (error) {
        // If getCurrentUser fails, at least we have tokens
        console.error('Failed to get user info after login:', error)
      }
      return response
    }

    const register = async (data: RegisterRequest) => {
      await AuthAPI.register(data)
      // Auto-login after registration
      return await login({ email: data.email, password: data.password })
    }

    const logout = async () => {
      try {
        await AuthAPI.logout()
      } catch (error) {
        console.error('Logout error:', error)
      } finally {
        clearAuth()
      }
    }

    const refreshUser = async () => {
      if (isAuth.value) {
        const userInfo = await AuthAPI.getCurrentUser()
        user.value = userInfo
      }
    }

    const loadSetupRequired = async (): Promise<boolean> => {
      const res = await AuthAPI.getSetupRequired()
      setupRequired.value = res.setup_required
      return res.setup_required
    }

    const bootstrapFirstAdmin = async (data: BootstrapRequest) => {
      const response = await AuthAPI.bootstrap(data)
      accessToken.value = response.access_token
      refreshToken.value = response.refresh_token ?? ''
      isAuthenticated.value = true
      setupRequired.value = false
      try {
        const userInfo = await AuthAPI.getCurrentUser()
        user.value = userInfo
      } catch (error) {
        console.error('Failed to get user info after bootstrap:', error)
        if (response.user) {
          user.value = {
            id: response.user.id,
            email: response.user.email,
            full_name: response.user.full_name,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          }
        }
      }
      return response
    }

    return {
      accessToken,
      refreshToken,
      user,
      isAuthenticated,
      isAuth,
      setupRequired,
      setAuth,
      clearAuth,
      updateToken,
      updateUser,
      login,
      register,
      logout,
      refreshUser,
      loadSetupRequired,
      bootstrapFirstAdmin,
    }
  },
  {
    // Do not persist setupRequired — always resolved from GET /auth/setup-required on load.
    persist: piniaPersistConfig('opspilot-auth', [
      'accessToken',
      'refreshToken',
      'user',
      'isAuthenticated',
    ]),
  }
)

// ============================================
// Organization Store
// ============================================

import { OrganizationsAPI } from '@/api/opspilot/organizations'
import type { Organization } from '@/api/opspilot/types'

export const useOpsPilotOrganizationStore = defineStore(
  'opspilot-organization',
  () => {
    const organizations = ref<Organization[]>([])
    const currentOrganization = ref<Organization | null>(null)
    const loading = ref<boolean>(false)

    const hasOrganizations = computed(() => organizations.value.length > 0)

    const fetchOrganizations = async () => {
      loading.value = true
      try {
        const response = await OrganizationsAPI.list()
        organizations.value = response.items

        // Set current organization if not set
        if (!currentOrganization.value && response.items.length > 0) {
          currentOrganization.value = response.items[0]
        }
      } finally {
        loading.value = false
      }
    }

    const setCurrentOrganization = (org: Organization) => {
      currentOrganization.value = org
    }

    const createOrganization = async (data: { name: string; slug: string; description?: string }) => {
      const org = await OrganizationsAPI.create(data)
      organizations.value.push(org)
      currentOrganization.value = org
      return org
    }

    const updateOrganization = async (id: string, data: { name?: string; slug?: string; description?: string }) => {
      const org = await OrganizationsAPI.update(id, data)
      const index = organizations.value.findIndex(o => o.id === id)
      if (index !== -1) {
        organizations.value[index] = org
      }
      if (currentOrganization.value?.id === id) {
        currentOrganization.value = org
      }
      return org
    }

    const deleteOrganization = async (id: string) => {
      await OrganizationsAPI.delete(id)
      organizations.value = organizations.value.filter(o => o.id !== id)
      if (currentOrganization.value?.id === id) {
        currentOrganization.value = organizations.value[0] || null
      }
    }

    const switchOrganization = async (id: string) => {
      await OrganizationsAPI.switchOrganization(id)
      const org = organizations.value.find(o => o.id === id)
      if (org) {
        currentOrganization.value = org
      }
    }

    return {
      organizations,
      currentOrganization,
      loading,
      hasOrganizations,
      fetchOrganizations,
      setCurrentOrganization,
      createOrganization,
      updateOrganization,
      deleteOrganization,
      switchOrganization,
    }
  },
  {
    persist: piniaPersistConfig('opspilot-organization'),
  }
)

// ============================================
// Server Store
// ============================================

import { ServersAPI } from '@/api/opspilot/servers'
import type { CreateServerRequest, Server } from '@/api/opspilot/types'

export const useOpsPilotServerStore = defineStore(
  'opspilot-server',
  () => {
    const servers = ref<Server[]>([])
    const currentServer = ref<Server | null>(null)
    const loading = ref<boolean>(false)

    const onlineServers = computed(() =>
      servers.value.filter(s => s.status === 'online' || s.status === 'active'),
    )
    const offlineServers = computed(() =>
      servers.value.filter(s => s.status !== 'online' && s.status !== 'active'),
    )

    const fetchServers = async (organizationId?: string) => {
      loading.value = true
      try {
        if (!organizationId) {
          servers.value = []
          return
        }
        const response = await ServersAPI.list(organizationId)
        servers.value = response.servers
      } finally {
        loading.value = false
      }
    }

    const setCurrentServer = (server: Server | null) => {
      currentServer.value = server
    }

    const createServer = async (organizationId: string, data: CreateServerRequest) => {
      const server = await ServersAPI.create(organizationId, data)
      servers.value.push(server)
      return server
    }

    const updateServer = async (id: string, data: { name?: string; tags?: string[] }) => {
      const server = await ServersAPI.update(id, data)
      const index = servers.value.findIndex(s => s.id === id)
      if (index !== -1) {
        servers.value[index] = server
      }
      if (currentServer.value?.id === id) {
        currentServer.value = server
      }
      return server
    }

    const deleteServer = async (id: string) => {
      await ServersAPI.delete(id)
      servers.value = servers.value.filter(s => s.id !== id)
      if (currentServer.value?.id === id) {
        currentServer.value = null
      }
    }

    const testConnection = async (id: string) => {
      return await ServersAPI.testConnection(id)
    }

    return {
      servers,
      currentServer,
      loading,
      onlineServers,
      offlineServers,
      fetchServers,
      setCurrentServer,
      createServer,
      updateServer,
      deleteServer,
      testConnection,
    }
  },
  {
    persist: piniaPersistConfig('opspilot-server'),
  }
)

// ============================================
// Alert Store
// ============================================

import { AlertsAPI } from '@/api/opspilot/alerts'
import type { Alert, AlertStats } from '@/api/opspilot/types'

export const useOpsPilotAlertStore = defineStore(
  'opspilot-alert',
  () => {
    const alerts = ref<Alert[]>([])
    const stats = ref<AlertStats | null>(null)
    const loading = ref<boolean>(false)

    const activeAlerts = computed(() => alerts.value.filter(a => !a.resolved))
    const criticalAlerts = computed(() => activeAlerts.value.filter(a => a.severity === 'critical'))
    const warningAlerts = computed(() => activeAlerts.value.filter(a => a.severity === 'warning'))

    const fetchAlerts = async (params?: {
      server_id?: string
      severity?: string
      resolved?: boolean
      start?: string
      end?: string
    }) => {
      loading.value = true
      try {
        const response = await AlertsAPI.list(params)
        alerts.value = response.items
      } finally {
        loading.value = false
      }
    }

    const fetchStats = async (params?: { start?: string; end?: string }) => {
      const response = await AlertsAPI.getStats(params)
      stats.value = response
      return response
    }

    const resolveAlert = async (id: string) => {
      const alert = await AlertsAPI.resolve(id)
      const index = alerts.value.findIndex(a => a.id === id)
      if (index !== -1) {
        alerts.value[index] = alert
      }
      return alert
    }

    const deleteAlert = async (id: string) => {
      await AlertsAPI.delete(id)
      alerts.value = alerts.value.filter(a => a.id !== id)
    }

    const createAlert = async (data: {
      server_id: string
      type: string
      severity: string
      title: string
      message: string
      threshold?: number
    }) => {
      const alert = await AlertsAPI.create(data)
      alerts.value.unshift(alert)
      return alert
    }

    return {
      alerts,
      stats,
      loading,
      activeAlerts,
      criticalAlerts,
      warningAlerts,
      fetchAlerts,
      fetchStats,
      resolveAlert,
      deleteAlert,
      createAlert,
    }
  },
  {
    persist: piniaPersistConfig('opspilot-alert'),
  }
)

// ============================================
// Dashboard Store
// ============================================

import { DashboardAPI } from '@/api/opspilot/index'
import type { DashboardStats, ServerHealthOverview, RecentAlert } from '@/api/opspilot/types'

export const useOpsPilotDashboardStore = defineStore('opspilot-dashboard', () => {
  const stats = ref<DashboardStats | null>(null)
  const serverHealth = ref<ServerHealthOverview[]>([])
  const recentAlerts = ref<RecentAlert[]>([])
  const loading = ref<boolean>(false)

  const fetchDashboard = async () => {
    loading.value = true
    try {
      const [dashboardStats, health, alerts] = await Promise.all([
        DashboardAPI.getStats(),
        DashboardAPI.getServerHealth(10),
        DashboardAPI.getRecentAlerts(10),
      ])

      stats.value = dashboardStats
      serverHealth.value = health
      recentAlerts.value = alerts
    } finally {
      loading.value = false
    }
  }

  return {
    stats,
    serverHealth,
    recentAlerts,
    loading,
    fetchDashboard,
  }
})

/**
 * Authenticated app routes rendered inside OpsPilotMainLayout (nested under `/`).
 */
import type { RouteRecordRaw } from 'vue-router'

export const mainLayoutChildren: RouteRecordRaw[] = [
  {
    path: 'dashboard',
    name: 'Dashboard',
    component: () => import('@/views/dashboard/index.vue'),
    meta: {
      title: 'Dashboard',
      requiresAuth: true,
      icon: 'Dashboard',
      isAffix: true,
      isKeepAlive: true,
    },
  },
  {
    path: 'servers',
    name: 'Servers',
    component: () => import('@/views/servers/index.vue'),
    meta: {
      title: 'Servers',
      requiresAuth: true,
      icon: 'Monitor',
      isKeepAlive: true,
    },
  },
  {
    path: 'servers/:id',
    name: 'ServerDetail',
    component: () => import('@/views/servers/detail/index.vue'),
    meta: {
      title: 'Server Detail',
      requiresAuth: true,
      activeMenu: '/servers',
      hidden: true,
    },
  },
  {
    path: 'alerts',
    name: 'Alerts',
    component: () => import('@/views/alerts/index.vue'),
    meta: {
      title: 'Alerts',
      requiresAuth: true,
      icon: 'Bell',
      isKeepAlive: true,
    },
  },
  {
    path: 'deployments',
    name: 'Deployments',
    component: () => import('@/views/deployments/index.vue'),
    meta: {
      title: 'Deployments',
      requiresAuth: true,
      icon: 'Promotion',
      isKeepAlive: true,
    },
  },
  {
    path: 'organizations',
    name: 'Organizations',
    component: () => import('@/views/organizations/index.vue'),
    meta: {
      title: 'Organizations',
      requiresAuth: true,
      icon: 'OfficeBuilding',
      isKeepAlive: true,
    },
  },
  {
    path: 'organizations/:id',
    name: 'OrganizationDetail',
    component: () => import('@/views/organizations/detail/index.vue'),
    meta: {
      title: 'Organization Detail',
      requiresAuth: true,
      activeMenu: '/organizations',
      hidden: true,
    },
  },
  {
    path: 'organizations/:id/settings',
    name: 'OrganizationSettings',
    component: () => import('@/views/organizations/settings/index.vue'),
    meta: {
      title: 'Organization Settings',
      requiresAuth: true,
      activeMenu: '/organizations',
      hidden: true,
    },
  },
  {
    path: 'settings',
    name: 'Settings',
    component: () => import('@/views/settings/index.vue'),
    meta: {
      title: 'Settings',
      requiresAuth: true,
      icon: 'Setting',
    },
  },
]

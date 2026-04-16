/**
 * OpsPilot Router Configuration
 * Vue Router setup with auth guards and routes
 */

import { createRouter, createWebHashHistory } from 'vue-router'
import { useOpsPilotAuthStore } from '@/stores/modules/opspilot'
import { ElMessage } from 'element-plus'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'

// Configure NProgress
NProgress.configure({
  showSpinner: false,
  trickleSpeed: 200,
})

// Route meta interface
interface RouteMeta {
  title?: string
  requiresAuth?: boolean
  layout?: string
  hidden?: boolean
  icon?: string
  activeMenu?: string
  isAffix?: boolean
  isKeepAlive?: boolean
  isFull?: boolean
}

// ============================================
// Route definitions
// ============================================

// Onboarding routes (public)
export const onboardingRoutes = [
  {
    path: '/onboarding',
    name: 'Onboarding',
    component: () => import('@/views/onboarding/index.vue'),
    meta: {
      title: 'Get Started',
      requiresAuth: false,
      hidden: true,
    } as RouteMeta,
  },
]

// Auth routes (public)
export const authRoutes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/login/index.vue'),
    meta: {
      title: 'Login',
      requiresAuth: false,
      hidden: true,
    } as RouteMeta,
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/auth/register/index.vue'),
    meta: {
      title: 'Register',
      requiresAuth: false,
      hidden: true,
    } as RouteMeta,
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: () => import('@/views/auth/forgot-password/index.vue'),
    meta: {
      title: 'Forgot Password',
      requiresAuth: false,
      hidden: true,
    } as RouteMeta,
  },
]

// Dashboard routes (protected)
export const dashboardRoutes = [
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/dashboard/index.vue'),
    meta: {
      title: 'Dashboard',
      requiresAuth: true,
      icon: 'Dashboard',
      isAffix: true,
      isKeepAlive: true,
    } as RouteMeta,
  },
]

// Server routes (protected)
export const serverRoutes = [
  {
    path: '/servers',
    name: 'Servers',
    component: () => import('@/views/servers/index.vue'),
    meta: {
      title: 'Servers',
      requiresAuth: true,
      icon: 'Monitor',
      isKeepAlive: true,
    } as RouteMeta,
  },
  {
    path: '/servers/:id',
    name: 'ServerDetail',
    component: () => import('@/views/servers/detail/index.vue'),
    meta: {
      title: 'Server Detail',
      requiresAuth: true,
      activeMenu: '/servers',
      hidden: true,
    } as RouteMeta,
  },
]

// Alert routes (protected)
export const alertRoutes = [
  {
    path: '/alerts',
    name: 'Alerts',
    component: () => import('@/views/alerts/index.vue'),
    meta: {
      title: 'Alerts',
      requiresAuth: true,
      icon: 'Bell',
      isKeepAlive: true,
    } as RouteMeta,
  },
]

// Deployment routes (protected)
export const deploymentRoutes = [
  {
    path: '/deployments',
    name: 'Deployments',
    component: () => import('@/views/deployments/index.vue'),
    meta: {
      title: 'Deployments',
      requiresAuth: true,
      icon: 'Promotion',
      isKeepAlive: true,
    } as RouteMeta,
  },
]

// Organization routes (protected)
export const organizationRoutes = [
  {
    path: '/organizations',
    name: 'Organizations',
    component: () => import('@/views/organizations/index.vue'),
    meta: {
      title: 'Organizations',
      requiresAuth: true,
      icon: 'OfficeBuilding',
      isKeepAlive: true,
    } as RouteMeta,
  },
  {
    path: '/organizations/:id',
    name: 'OrganizationDetail',
    component: () => import('@/views/organizations/detail/index.vue'),
    meta: {
      title: 'Organization Detail',
      requiresAuth: true,
      activeMenu: '/organizations',
      hidden: true,
    } as RouteMeta,
  },
  {
    path: '/organizations/:id/settings',
    name: 'OrganizationSettings',
    component: () => import('@/views/organizations/settings/index.vue'),
    meta: {
      title: 'Organization Settings',
      requiresAuth: true,
      activeMenu: '/organizations',
      hidden: true,
    } as RouteMeta,
  },
]

// Settings routes (protected)
export const settingsRoutes = [
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/settings/index.vue'),
    meta: {
      title: 'Settings',
      requiresAuth: true,
      icon: 'Setting',
    } as RouteMeta,
  },
]

// Error routes
export const errorRoutes = [
  {
    path: '/404',
    name: '404',
    component: () => import('@/views/error/404.vue'),
    meta: {
      title: '404 Not Found',
      requiresAuth: false,
      hidden: true,
    } as RouteMeta,
  },
  {
    path: '/500',
    name: '500',
    component: () => import('@/views/error/500.vue'),
    meta: {
      title: '500 Server Error',
      requiresAuth: false,
      hidden: true,
    } as RouteMeta,
  },
]

// Combine all routes
const routes = [
  {
    path: '/',
    redirect: '/dashboard',
    meta: {
      hidden: true,
    } as RouteMeta,
  },
  ...authRoutes,
  ...dashboardRoutes,
  ...serverRoutes,
  ...alertRoutes,
  ...deploymentRoutes,
  ...organizationRoutes,
  ...settingsRoutes,
  ...errorRoutes,
  {
    path: '/:pathMatch(.*)*',
    redirect: '/404',
    meta: {
      hidden: true,
    } as RouteMeta,
  },
]

// ============================================
// Router setup
// ============================================

const router = createRouter({
  history: createWebHashHistory(),
  routes,
  scrollBehavior: () => ({ left: 0, top: 0 }),
})

// ============================================
// Navigation guards
// ============================================

/**
 * Route guard: Check authentication
 */
router.beforeEach(async (to, from, next) => {
  // Start progress bar
  NProgress.start()

  // Set page title
  const appTitle = import.meta.env.VITE_GLOB_APP_TITLE || 'OpsPilot'
  document.title = to.meta.title ? `${to.meta.title} - ${appTitle}` : appTitle

  // Get auth store
  const authStore = useOpsPilotAuthStore()

  // Check if route requires authentication
  const requiresAuth = to.meta.requiresAuth !== false

  // If accessing login/register page and already authenticated, redirect to dashboard
  if (['Login', 'Register'].includes(to.name as string) && authStore.isAuth) {
    ElMessage.info('You are already logged in')
    return next('/dashboard')
  }

  // If route requires auth and user is not authenticated, redirect to login
  if (requiresAuth && !authStore.isAuth) {
    ElMessage.warning('Please login first')
    return next({
      path: '/login',
      query: { redirect: to.fullPath },
    })
  }

  // If accessing protected route, ensure user data is loaded
  if (requiresAuth && authStore.isAuth && !authStore.user) {
    try {
      await authStore.refreshUser()
    } catch (error) {
      console.error('Failed to refresh user:', error)
      authStore.clearAuth()
      return next('/login')
    }
  }

  // Check for first-time user - redirect to onboarding
  if (authStore.isAuth && authStore.user?.is_first_time === true) {
    // Only redirect to onboarding if not already there
    if (to.name !== 'Onboarding') {
      return next('/onboarding')
    }
  }

  // Proceed to route
  next()
})

/**
 * After route change
 */
router.afterEach(() => {
  // Stop progress bar
  NProgress.done()
})

/**
 * Route error handler
 */
router.onError(error => {
  NProgress.done()
  console.error('Router error:', error)
})

// ============================================
// Helper functions
// ============================================

/**
 * Get all routes for menu generation
 */
export const getMenuRoutes = () => {
  return routes.filter(
    route => !route.meta?.hidden && route.meta?.requiresAuth !== false && route.name && typeof route.name === 'string'
  )
}

/**
 * Check if route exists
 */
export const hasRoute = (name: string) => {
  return router.hasRoute(name)
}

export default router

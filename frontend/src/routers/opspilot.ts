/**
 * OpsPilot Router Configuration
 * Vue Router setup with auth guards and routes
 */

import { createRouter, createWebHashHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

import { mainLayoutChildren } from './main-layout-routes'
import { useOpsPilotAuthStore, useOpsPilotOrganizationStore } from '@/stores/modules/opspilot'
import { ElMessage } from 'element-plus'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'

// Configure NProgress
NProgress.configure({
  showSpinner: false,
  trickleSpeed: 200,
})

// ============================================
// Route definitions
// ============================================

// Onboarding (authenticated first-time setup only)
export const onboardingRoutes: RouteRecordRaw[] = [
  {
    path: '/onboarding',
    name: 'Onboarding',
    component: () => import('@/views/onboarding/index.vue'),
    meta: {
      title: 'Get Started',
      requiresAuth: true,
      hidden: true,
    },
  },
]

// Auth routes (public)
export const authRoutes: RouteRecordRaw[] = [
  {
    path: '/setup',
    name: 'Setup',
    component: () => import('@/views/setup/index.vue'),
    meta: {
      title: 'Initial setup',
      requiresAuth: false,
      hidden: true,
    },
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/login/index.vue'),
    meta: {
      title: 'Login',
      requiresAuth: false,
      hidden: true,
    },
  },
  {
    path: '/register',
    redirect: '/login',
    meta: {
      title: 'Register',
      requiresAuth: false,
      hidden: true,
    },
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: () => import('@/views/auth/forgot-password/index.vue'),
    meta: {
      title: 'Forgot Password',
      requiresAuth: false,
      hidden: true,
    },
  },
]

// Error routes
export const errorRoutes: RouteRecordRaw[] = [
  {
    path: '/404',
    name: '404',
    component: () => import('@/views/error/404.vue'),
    meta: {
      title: '404 Not Found',
      requiresAuth: false,
      hidden: true,
    },
  },
  {
    path: '/500',
    name: '500',
    component: () => import('@/views/error/500.vue'),
    meta: {
      title: '500 Server Error',
      requiresAuth: false,
      hidden: true,
    },
  },
]

/** Shell layout: top navigation + main content (nested paths under `/`). */
const mainLayoutRoute: RouteRecordRaw = {
  path: '/',
  component: () => import('@/layouts/OpsPilotMainLayout.vue'),
  redirect: '/dashboard',
  meta: {
    requiresAuth: true,
    hidden: true,
  },
  children: mainLayoutChildren,
}

// Combine all routes
const routes: RouteRecordRaw[] = [
  ...authRoutes,
  ...onboardingRoutes,
  mainLayoutRoute,
  ...errorRoutes,
  {
    path: '/:pathMatch(.*)*',
    redirect: '/404',
    meta: {
      hidden: true,
    },
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

  // Fresh install: force first-admin wizard until a user exists
  if (authStore.setupRequired === null) {
    try {
      await authStore.loadSetupRequired()
    } catch (err) {
      // Do not assume setup is done on network/CORS/5xx — that hides the wizard entirely.
      console.error('GET /auth/setup-required failed:', err)
      authStore.$patch({ setupRequired: true })
    }
  }
  const needsSetup = authStore.setupRequired === true
  const isSetupRoute = to.name === 'Setup'
  if (needsSetup && !isSetupRoute) {
    return next({ path: '/setup', replace: true })
  }
  if (!needsSetup && isSetupRoute) {
    return next({ path: '/login', replace: true })
  }

  // Only protect routes that explicitly set requiresAuth: true (default is public)
  const requiresAuth = to.meta.requiresAuth === true

  // If accessing login page and already authenticated, redirect to dashboard
  if (to.name === 'Login' && authStore.isAuth) {
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

  // Organization context: load memberships and send users without any org to onboarding
  if (requiresAuth && authStore.isAuth) {
    const skipOrgGate = to.name === 'Onboarding' || to.name === 'Setup'
    if (!skipOrgGate) {
      const orgStore = useOpsPilotOrganizationStore()
      try {
        await orgStore.fetchOrganizations()
      } catch (err) {
        console.error('Failed to load organizations:', err)
      }
      if (orgStore.organizations.length === 0) {
        return next({ path: '/onboarding', replace: true })
      }
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
export const getMenuRoutes = (): RouteRecordRaw[] => {
  return mainLayoutChildren.filter(
    route => !route.meta?.hidden && route.meta?.requiresAuth !== false && route.name && typeof route.name === 'string',
  )
}

/**
 * Check if route exists
 */
export const hasRoute = (name: string) => {
  return router.hasRoute(name)
}

export default router

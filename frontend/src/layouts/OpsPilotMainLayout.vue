<template>
  <div class="opspilot-shell">
    <header class="top-bar">
      <div class="top-bar__start">
        <router-link to="/dashboard" class="brand" @click.stop>
          <span class="brand-mark" aria-hidden="true" />
          <span class="brand-text">OpsPilot</span>
        </router-link>

        <el-dropdown
          v-if="!isWideNav"
          trigger="click"
          class="nav-route-dropdown-wrap"
          popper-class="nav-route-dropdown"
          placement="bottom-start"
          @command="onNavRouteCommand"
        >
          <el-button class="nav-toggle" text aria-label="Open navigation menu" aria-haspopup="true">
            <el-icon :size="22"><Menu /></el-icon>
            <span class="nav-toggle__label">Menu</span>
            <el-icon class="nav-toggle__caret"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item
                v-for="item in visibleMenuRoutes"
                :key="String(item.name)"
                :command="menuIndex(item)"
                :class="{ 'is-nav-active': isNavItemActive(item) }"
              >
                <span class="nav-dd-row">
                  <el-icon v-if="menuIcon(item.meta?.icon as string)" class="nav-dd-icon">
                    <component :is="menuIcon(item.meta?.icon as string)" />
                  </el-icon>
                  <span>{{ item.meta?.title }}</span>
                </span>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>

      <div v-if="isWideNav" class="top-menu-wrap">
        <el-menu
          mode="horizontal"
          :ellipsis="false"
          :router="true"
          class="top-menu top-menu--desktop"
          :default-active="activeMenuPath"
          background-color="transparent"
        >
          <template v-for="item in visibleMenuRoutes" :key="String(item.name)">
            <el-menu-item :index="menuIndex(item)">
              <el-icon v-if="menuIcon(item.meta?.icon as string)">
                <component :is="menuIcon(item.meta?.icon as string)" />
              </el-icon>
              <span class="menu-item__label">{{ item.meta?.title }}</span>
            </el-menu-item>
          </template>
        </el-menu>
      </div>

      <div v-else class="top-menu-spacer" aria-hidden="true" />

      <div class="top-actions">
        <span
          v-if="authStore.user?.email"
          class="user-email user-email--bar"
          :title="authStore.user.email"
        >
          {{ authStore.user.email }}
        </span>
        <el-dropdown trigger="click" @command="onUserCommand">
          <el-button text class="user-trigger" aria-label="Account menu">
            <el-icon><User /></el-icon>
            <el-icon class="caret"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu class="account-dropdown-menu">
              <el-dropdown-item v-if="authStore.user?.email" disabled class="dropdown-email-item">
                <span class="dropdown-email-text">{{ authStore.user.email }}</span>
              </el-dropdown-item>
              <el-dropdown-item command="settings">Settings</el-dropdown-item>
              <el-dropdown-item divided command="logout">Log out</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>

    <main class="main-area">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useMediaQuery } from '@vueuse/core'
import { User, ArrowDown, Menu, Odometer, Monitor, Bell, Promotion, OfficeBuilding, Setting } from '@element-plus/icons-vue'
import { useOpsPilotAuthStore } from '@/stores/modules/opspilot'
import { mainLayoutChildren } from '@/routers/main-layout-routes'

/** Horizontal nav at lg+; narrower viewports use Menu dropdown (updates on resize). */
const isWideNav = useMediaQuery('(min-width: 1024px)')

const route = useRoute()
const router = useRouter()
const authStore = useOpsPilotAuthStore()

function onNavRouteCommand(path: string) {
  void router.push(path)
}

const ICON_MAP: Record<string, typeof Odometer> = {
  Dashboard: Odometer,
  Monitor,
  Bell,
  Promotion,
  OfficeBuilding,
  Setting,
}

function menuIcon(metaIcon?: string) {
  if (!metaIcon) return undefined
  return ICON_MAP[metaIcon]
}

const visibleMenuRoutes = computed(() =>
  mainLayoutChildren.filter(
    r =>
      !r.meta?.hidden &&
      r.meta?.requiresAuth !== false &&
      r.name &&
      typeof r.name === 'string',
  ) as RouteRecordRaw[],
)

const activeMenuPath = computed(() => {
  const m = route.meta?.activeMenu as string | undefined
  return m || route.path
})

/** Full path for el-menu router (nested routes use absolute paths). */
function menuIndex(item: RouteRecordRaw): string {
  const p = item.path.startsWith('/') ? item.path : `/${item.path}`
  return p
}

function isNavItemActive(item: RouteRecordRaw): boolean {
  return activeMenuPath.value === menuIndex(item)
}

async function onUserCommand(cmd: string) {
  if (cmd === 'logout') {
    await authStore.logout()
    await router.push('/login')
    return
  }
  if (cmd === 'settings') {
    await router.push('/settings')
  }
}
</script>

<style scoped lang="scss">
.opspilot-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f1f2f3;
}

html.dark .opspilot-shell {
  background: #0d0e12;
}

.top-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 56px;
  max-height: 56px;
  padding: 0 16px 0 20px;
  flex-shrink: 0;
  background: #ffffff;
  border-bottom: 1px solid #d5d7db;
  box-shadow: 0 1px 0 rgba(21, 24, 30, 0.04);
  flex-wrap: nowrap;
}

.top-bar__start {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.nav-route-dropdown-wrap {
  flex-shrink: 0;
}

.nav-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin: 0 0 0 4px;
  padding: 8px 10px;
  color: #15181e;
  border-radius: 8px;
}

.nav-toggle__label {
  font-size: 0.875rem;
  font-weight: 600;
}

.nav-toggle__caret {
  font-size: 12px;
  margin-left: -2px;
}

html.dark .nav-toggle {
  color: #ffffff;
}

html.dark .top-bar {
  background: #15181e;
  border-bottom-color: rgba(255, 255, 255, 0.08);
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: #15181e;
  font-weight: 700;
  font-size: 1.125rem;
  letter-spacing: -0.02em;
  padding-right: 4px;
  flex-shrink: 0;
  min-width: 0;
}

html.dark .brand {
  color: #ffffff;
}

.brand-mark {
  width: 8px;
  height: 28px;
  border-radius: 2px;
  background: linear-gradient(180deg, #14c6cb 0%, #1868f2 100%);
}

.brand-text {
  font-family:
    system-ui,
    -apple-system,
    BlinkMacSystemFont,
    'Segoe UI',
    sans-serif;
}

/* Middle column: takes remaining width only; menu scrolls inside — never overlaps account */
.top-menu-spacer {
  flex: 1 1 0%;
  min-width: 0;
}

.top-menu-wrap {
  flex: 1 1 0%;
  min-width: 0;
  overflow: hidden;
  display: flex;
  align-items: stretch;
}

.top-menu {
  flex: 1;
  width: 100%;
  min-width: 0;
  border-bottom: none !important;
  height: 56px;
}

.top-menu :deep(.el-menu--horizontal) {
  flex-wrap: nowrap;
  border-bottom: none;
}

.top-menu :deep(.el-menu--horizontal.el-menu) {
  overflow-x: auto;
  overflow-y: hidden;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: thin;
  max-width: 100%;
}

.top-menu :deep(.el-menu--horizontal::-webkit-scrollbar) {
  height: 4px;
}

.top-menu :deep(.el-menu--horizontal::-webkit-scrollbar-thumb) {
  background: rgba(21, 24, 30, 0.2);
  border-radius: 4px;
}

html.dark .top-menu :deep(.el-menu--horizontal::-webkit-scrollbar-thumb) {
  background: rgba(255, 255, 255, 0.2);
}

.top-menu :deep(.el-menu-item) {
  font-weight: 500;
  flex-shrink: 0;
}

.menu-item__label {
  white-space: nowrap;
}

.top-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 0 0 auto;
  flex-shrink: 0;
  min-width: 0;
  padding-left: 10px;
  margin-left: 0;
  position: relative;
  z-index: 2;
  background: #ffffff;
  box-shadow: -10px 0 18px -6px #ffffff;
}

html.dark .top-actions {
  background: #15181e;
  box-shadow: -10px 0 18px -6px #15181e;
}

.user-email--bar {
  display: block;
  font-size: 0.8125rem;
  color: #656a76;
  flex: 0 1 auto;
  min-width: 0;
  max-width: 10rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

html.dark .user-email--bar {
  color: #b2b6bd;
}

/* Long emails: hide bar copy so nav never fights for width; full address in dropdown + title */
@media (max-width: 1400px) {
  .user-email--bar {
    display: none;
  }
}

.user-trigger {
  padding: 8px 10px;
  color: #15181e;
}

html.dark .user-trigger {
  color: #ffffff;
}

.user-trigger .caret {
  margin-left: 2px;
  font-size: 12px;
}

.main-area {
  flex: 1;
  min-height: 0;
  width: 100%;
  max-width: 100vw;
  box-sizing: border-box;
}

/* Tablet: tighter header, optional icon-first density */
@media (max-width: 991px) {
  .top-bar {
    padding: 0 10px 0 12px;
    gap: 4px;
    min-height: 52px;
    max-height: 52px;
  }

  .brand {
    font-size: 1rem;
    gap: 8px;
  }

  .brand-mark {
    height: 24px;
  }

  .top-menu {
    height: 52px;
  }

  .top-menu :deep(.el-menu-item) {
    padding: 0 12px;
    height: 52px;
    line-height: 52px;
  }
}

@media (max-width: 767px) {
  .top-bar {
    min-height: 52px;
    max-height: 52px;
    padding: 0 8px 0 10px;
  }

  .top-actions {
    margin-left: auto;
    box-shadow: none;
    padding-left: 8px;
  }

  .brand-text {
    max-width: 38vw;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .nav-toggle__label {
    display: none;
  }

  .nav-toggle__caret {
    display: none;
  }

  .nav-toggle {
    padding: 8px;
  }
}

@media (max-width: 479px) {
  .top-actions {
    gap: 6px;
  }

  .user-trigger .caret {
    display: none;
  }
}

</style>

<!-- Teleported dropdown popper -->
<style lang="scss">
.nav-route-dropdown {
  min-width: 200px;
}

.nav-route-dropdown .nav-dd-row {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.nav-route-dropdown .nav-dd-icon {
  font-size: 18px;
}

.nav-route-dropdown .el-dropdown-menu__item.is-nav-active {
  color: var(--el-color-primary);
  font-weight: 600;
  background-color: var(--el-color-primary-light-9);
}

html.dark .nav-route-dropdown .el-dropdown-menu__item.is-nav-active {
  background-color: rgba(20, 198, 203, 0.12);
}

.account-dropdown-menu .dropdown-email-item {
  cursor: default;
  opacity: 1;
  color: #656a76;
  background: transparent !important;
}

.account-dropdown-menu .dropdown-email-item.is-disabled {
  opacity: 1;
}

.account-dropdown-menu .dropdown-email-text {
  display: block;
  font-size: 0.75rem;
  line-height: 1.35;
  word-break: break-all;
  max-width: 260px;
  white-space: normal;
}

html.dark .account-dropdown-menu .dropdown-email-item {
  color: #b2b6bd;
}
</style>

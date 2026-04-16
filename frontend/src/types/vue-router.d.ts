import 'vue-router'

declare module 'vue-router' {
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
}

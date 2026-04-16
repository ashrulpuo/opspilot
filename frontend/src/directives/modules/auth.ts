/**
 * v-auth
 * Authentication directive
 * Shows/hides elements based on user authentication
 */
import { useOpsPilotAuthStore } from '@/stores/modules/opspilot'
import type { Directive, DirectiveBinding } from 'vue'

const auth: Directive = {
  mounted(el: HTMLElement, binding: DirectiveBinding) {
    const { value } = binding
    const authStore = useOpsPilotAuthStore()

    // Check if user is authenticated
    const isAuthenticated = authStore.isAuth

    // If no value specified, just check authentication
    if (!value) {
      if (!isAuthenticated) {
        el.remove()
      }
      return
    }

    // If value is an array of roles/permissions (future enhancement)
    if (Array.isArray(value) && value.length) {
      // For now, just check authentication
      // In the future, implement role-based access control
      if (!isAuthenticated) {
        el.remove()
      }
    } else {
      // Single permission check
      if (!isAuthenticated) {
        el.remove()
      }
    }
  },
}

export default auth

import { computed } from 'vue'
import { defineStore } from 'pinia'
import { useOpsPilotServerStore } from '@/stores/modules/opspilot'
import type { Server } from '@/api/opspilot/types'

/**
 * Server detail views expect `servers[serverId]`. The main app store keeps a flat list
 * (`useOpsPilotServerStore`); this store exposes a convenient id map.
 */
export const useServerStore = defineStore('server-id-map', () => {
  const ops = useOpsPilotServerStore()

  const servers = computed((): Record<string, Server> => {
    const map: Record<string, Server> = {}
    for (const s of ops.servers) {
      map[s.id] = s
    }
    return map
  })

  return { servers }
})

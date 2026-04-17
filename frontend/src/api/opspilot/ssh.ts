/**
 * OpsPilot SSH Terminal API
 * SSH terminal endpoints (WebSocket)
 */

import request from './client'
import { sshTerminalWebSocketUrl } from './commands'

export const SSHTerminalAPI = {
  /**
   * Create new SSH session
   */
  createSession: (serverId: string): Promise<{ session_id: string; server_id: string; status: string }> => {
    return request.post<{ session_id: string; server_id: string; status: string }>(`/servers/${serverId}/ssh/sessions`)
  },

  /**
   * List SSH sessions for server
   */
  listSessions: (serverId: string): Promise<{ server_id: string; sessions: any[] }> => {
    return request.get<{ server_id: string; sessions: any[] }>(`/servers/${serverId}/ssh/sessions`)
  },

  /**
   * Terminate SSH session
   */
  terminateSession: (sessionId: string): Promise<{ message: string; session_id: string }> => {
    return request.post<{ message: string; session_id: string }>(`/ssh/sessions/${sessionId}/terminate`)
  },

  /**
   * Connect to SSH terminal via WebSocket
   * Returns WebSocket URL
   */
  getTerminalWebSocketURL: (sessionId: string): string => {
    return sshTerminalWebSocketUrl(sessionId)
  },
}

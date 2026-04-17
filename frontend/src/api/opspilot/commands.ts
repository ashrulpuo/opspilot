/**
 * OpsPilot Commands API
 * Command execution and SSH terminal endpoints
 */

import request, { API_BASE_URL } from './client'
import type { Command, SSHSession, PaginatedResponse } from './types'

/** WebSocket URL for the SSH terminal (must match `app.api.v1.ssh` router). */
export function sshTerminalWebSocketUrl(sessionId: string): string {
  const base = API_BASE_URL.trim().replace(/\/+$/, '')
  const wsOrigin = base.toLowerCase().startsWith('https://')
    ? `wss://${base.slice(8)}`
    : base.toLowerCase().startsWith('http://')
      ? `ws://${base.slice(7)}`
      : `ws://${base}`
  return `${wsOrigin}/api/v1/ssh/terminal/${encodeURIComponent(sessionId)}`
}

export const CommandsAPI = {
  /**
   * Execute command on server
   */
  execute: (data: {
    server_id: string
    command: string
    timeout_seconds?: number
  }): Promise<{ command_id: string; server_id: string; command: string; status: string }> => {
    return request.post<{ command_id: string; server_id: string; command: string; status: string }>(
      '/commands/execute',
      data
    )
  },

  /**
   * Get command by ID
   */
  get: (id: string): Promise<Command> => {
    return request.get<Command>(`/commands/${id}`)
  },

  /**
   * List commands for server
   */
  list: (params?: {
    page?: number
    page_size?: number
    server_id?: string
    status_filter?: string
  }): Promise<PaginatedResponse<Command>> => {
    return request.get<PaginatedResponse<Command>>('/commands', { params })
  },
}

export const SSHTerminalAPI = {
  /**
   * Create SSH session
   */
  createSession: (serverId: string): Promise<SSHSession> => {
    return request.post<SSHSession>(`/servers/${serverId}/ssh/sessions`, { server_id: serverId })
  },

  /**
   * Get SSH session status
   */
  getSession: (sessionId: string): Promise<SSHSession> => {
    return request.get<SSHSession>(`/ssh/sessions/${sessionId}`)
  },

  /**
   * Terminate SSH session
   */
  terminateSession: (sessionId: string): Promise<{ message: string; session_id: string }> => {
    return request.post<{ message: string; session_id: string }>(`/ssh/sessions/${sessionId}/terminate`)
  },

  /**
   * Connect to SSH WebSocket
   */
  connect: (sessionId: string): WebSocket => {
    return new WebSocket(sshTerminalWebSocketUrl(sessionId))
  },
}

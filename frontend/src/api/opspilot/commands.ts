/**
 * OpsPilot Commands API
 * Command execution and SSH terminal endpoints
 */

import request from '../opspilot/client'
import type { Command, SSHSession, PaginatedResponse } from './types'

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
  terminateSession: (sessionId: string): Promise<void> => {
    return request.delete<void>(`/ssh/sessions/${sessionId}`)
  },

  /**
   * Connect to SSH WebSocket
   */
  connect: (sessionId: string): WebSocket => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/api/v1/ssh/ws/${sessionId}`
    return new WebSocket(wsUrl)
  },
}

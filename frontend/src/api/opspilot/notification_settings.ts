/**
 * Notification Settings API
 */
import request from './client'

export interface SmtpConfig {
  id: string
  organization_id: string
  host: string
  port: number
  username: string
  from_address: string
  use_tls: boolean
  enabled: boolean
}

export interface SmtpConfigRequest {
  host: string
  port: number
  username: string
  password: string
  from_address: string
  use_tls: boolean
  enabled: boolean
}

export interface NotificationRecipient {
  id: string
  organization_id: string
  email: string
  name: string | null
  severity_filter: string
  enabled: boolean
  created_at: string
}

export interface RecipientRequest {
  email: string
  name?: string
  severity_filter: string
  enabled: boolean
}

export const NotificationSettingsAPI = {
  getSmtp: (): Promise<SmtpConfig | null> => request.get<SmtpConfig | null>('/notification-settings/smtp'),

  saveSmtp: (data: SmtpConfigRequest): Promise<SmtpConfig> =>
    request.put<SmtpConfig>('/notification-settings/smtp', data),

  testSmtp: (to_email: string): Promise<{ message: string }> =>
    request.post<{ message: string }>('/notification-settings/smtp/test', { to_email }),

  listRecipients: (): Promise<NotificationRecipient[]> =>
    request.get<NotificationRecipient[]>('/notification-settings/recipients'),

  addRecipient: (data: RecipientRequest): Promise<NotificationRecipient> =>
    request.post<NotificationRecipient>('/notification-settings/recipients', data),

  updateRecipient: (id: string, data: RecipientRequest): Promise<NotificationRecipient> =>
    request.patch<NotificationRecipient>(`/notification-settings/recipients/${id}`, data),

  deleteRecipient: (id: string): Promise<void> => request.delete<void>(`/notification-settings/recipients/${id}`),
}

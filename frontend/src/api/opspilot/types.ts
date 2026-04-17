/**
 * OpsPilot API Types
 * TypeScript interfaces for backend API responses
 */

// ============================================
// Common Types
// ============================================

export interface ApiResponse<T = any> {
  success: boolean
  message: string
  data: T
  code: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface ErrorResponse {
  success: false
  message: string
  code: number
  details?: any
}

// ============================================
// Auth Types
// ============================================

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  confirm_password: string
  full_name: string
}

/** First-admin fresh install (optional org display name). */
export interface BootstrapRequest extends RegisterRequest {
  organization_name?: string
}

export interface SetupRequiredResponse {
  setup_required: boolean
}

export interface ForgotPasswordRequest {
  email: string
}

export interface ResetPasswordRequest {
  token: string
  new_password: string
}

export interface LoginResponse {
  access_token: string
  token_type?: string
  user?: {
    id: string
    email: string
    full_name: string
  }
  refresh_token?: string
  expires_in?: number
}

export interface RefreshTokenResponse {
  access_token: string
  refresh_token: string
  expires_in: number
}

export interface User {
  id: string
  email: string
  full_name?: string
  avatar_url?: string
  is_first_time?: boolean
  created_at: string
  updated_at: string
  organizations?: Organization[]
}

// ============================================
// Organization Types
// ============================================

export interface Organization {
  id: string
  name: string
  slug: string
  description?: string
  logo_url?: string
  created_by: string
  created_at: string
  updated_at: string
}

export interface OrganizationMember {
  id: string
  user_id: string
  organization_id: string
  role: 'owner' | 'admin' | 'member' | 'viewer'
  user: {
    id: string
    email: string
    full_name?: string
    avatar_url?: string
  }
  created_at: string
}

export interface CreateOrganizationRequest {
  name: string
  slug: string
  description?: string
}

export interface UpdateOrganizationRequest {
  name?: string
  slug?: string
  description?: string
  logo_url?: string
}

// ============================================
// Server Types
// ============================================

export interface Server {
  id: string
  organization_id: string
  hostname: string
  ip_address: string
  os_type: string
  web_server_type?: string
  domain_name?: string
  status: string
  /** True when SSH username + encrypted password are saved (password never returned in API). */
  has_ssh_credentials?: boolean
  created_at: string
  updated_at: string
  /** Last successful push-agent metrics POST (ISO8601), if any. */
  agent_last_seen_at?: string | null
}

export interface ServerSshInstallCredentials {
  username: string
  password: string
  port?: number
}

export interface CreateServerRequest {
  hostname: string
  ip_address: string
  os_type: string
  domain_name?: string
  web_server_type?: string
  /** When true (linux only), backend SSH-installs the push agent; requires `ssh`. */
  auto_install_agent?: boolean
  ssh?: ServerSshInstallCredentials
}

export interface UpdateServerRequest {
  hostname?: string
  ip_address?: string
  domain_name?: string
  web_server_type?: string
  status?: string
}

export interface ApplyStateRequest {
  state: string
  test?: boolean
}

export interface ApplyStateResponse {
  server_id: string
  state: string
  test: boolean
  result: any
}

export interface ServerMetrics {
  server_id: string
  timestamp: string
  cpu_usage_percent: number
  memory_usage_percent: number
  disk_usage_percent: number
  network_in_bps?: number
  network_out_bps?: number
  load_average?: number[]
  uptime_seconds?: number
}

export interface BackupReport {
  server_id: string
  organization_id: string
  backup_results: any
}

export interface HealthReport {
  server_id: string
  organization_id: string
  checks: any
  overall_status: string
}

// ============================================
// Alert Types
// ============================================

export interface Alert {
  id: string
  server_id: string
  organization_id: string
  type: 'cpu' | 'memory' | 'disk' | 'network' | 'service' | 'system'
  severity: 'info' | 'warning' | 'critical'
  title: string
  message: string
  value?: number
  threshold?: number
  resolved: boolean
  resolved_at?: string
  created_at: string
}

export interface CreateAlertRequest {
  server_id: string
  type: 'cpu' | 'memory' | 'disk' | 'network' | 'service' | 'system'
  severity: 'info' | 'warning' | 'critical'
  title: string
  message: string
  threshold?: number
}

export interface AlertStats {
  total: number
  active: number
  resolved: number
  critical: number
  warning: number
}

// ============================================
// Command Types
// ============================================

export interface Command {
  id: string
  server_id: string
  command: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  output?: string
  error?: string
  exit_code?: number
  duration_seconds?: number
  created_by: string
  created_at: string
  updated_at: string
}

export interface ExecuteCommandRequest {
  server_id: string
  command: string
  timeout_seconds?: number
}

// ============================================
// Service Types
// ============================================

export interface Service {
  id: string
  server_id: string
  name: string
  display_name?: string
  status: 'running' | 'stopped' | 'failed' | 'unknown'
  enabled: boolean
  auto_restart: boolean
  cpu_percent?: number
  memory_mb?: number
  uptime_seconds?: number
  pid?: number
  created_at: string
  updated_at: string
}

export interface ServiceActionRequest {
  action: 'start' | 'stop' | 'restart' | 'enable' | 'disable'
}

// ============================================
// Credential Types
// ============================================

export interface Credential {
  id: string
  server_id: string
  server_hostname?: string
  name: string
  type: 'ssh_key' | 'password' | 'api_key' | 'token' | 'unknown'
  description?: string
  encrypted_data?: string
  nonce?: string
  salt?: string
  created_at: string
  updated_at: string
}

export interface CreateCredentialRequest {
  server_id: string
  name: string
  type: 'ssh_key' | 'password' | 'api_key' | 'token'
  data?: Record<string, any>
  encrypted_data?: string
  nonce?: string
  salt?: string
  description?: string
}

export interface UpdateCredentialRequest {
  name?: string
  description?: string
  data?: Record<string, any>
  encrypted_data?: string
  nonce?: string
  salt?: string
}

export interface EncryptedCredential {
  encrypted_data: string
  nonce: string
  salt: string
}

// ============================================
// Backup Types
// ============================================

export interface BackupSchedule {
  id: string
  server_id: string
  server_hostname?: string
  organization_id: string
  name: string
  source_paths: string[]
  destination: string
  schedule_type: 'hourly' | 'daily' | 'weekly' | 'monthly'
  schedule_value?: number
  retention_days: number
  enabled: boolean
  compress: boolean
  encrypt: boolean
  description?: string
  created_at: string
  updated_at: string
}

export interface BackupHistory {
  id: string
  backup_schedule_id?: string
  schedule_name?: string
  server_id: string
  server_hostname?: string
  organization_id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  started_at: string
  completed_at?: string
  duration_seconds?: number
  files_transferred?: number
  bytes_transferred?: number
  checksum?: string
  error_message?: string
}

export interface CreateBackupScheduleRequest {
  server_id: string
  name: string
  source_paths: string[]
  destination: string
  schedule_type: 'hourly' | 'daily' | 'weekly' | 'monthly'
  schedule_value?: number
  retention_days: number
  enabled: boolean
  compress?: boolean
  encrypt?: boolean
  description?: string
}

export interface UpdateBackupScheduleRequest {
  name?: string
  source_paths?: string[]
  destination?: string
  schedule_type?: 'hourly' | 'daily' | 'weekly' | 'monthly'
  schedule_value?: number
  retention_days?: number
  enabled?: boolean
  compress?: boolean
  encrypt?: boolean
  description?: string
}

// ============================================
// Command Types
// ============================================

export interface Command {
  id: string
  server_id: string
  server_hostname?: string
  command: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  output?: string
  error?: string
  exit_code?: number
  duration_seconds?: number
  created_at: string
  updated_at: string
}

export interface SSHSession {
  id: string
  server_id: string
  server_hostname?: string
  status: 'created' | 'active' | 'closed'
  created_at: string
  updated_at?: string
}

// ============================================
// Log Types
// ============================================

export interface Log {
  id: string
  server_id: string
  server_hostname?: string
  organization_id: string
  log_level: 'error' | 'warning' | 'info' | 'debug'
  log_type: string // e.g., 'system', 'application', 'security'
  message: string
  timestamp: string
  source?: string // e.g., 'nginx', 'mysql'
}

export interface LogStats {
  total: number
  error: number
  warning: number
  info: number
  debug: number
  recent_errors: number
  recent_warnings: number
}

// ============================================
// Deployment Types
// ============================================

export interface Deployment {
  id: string
  server_id: string
  server_hostname?: string
  organization_id: string
  name: string
  description?: string
  deployment_type: 'manual' | 'scheduled' | 'git' | 'docker'
  status: 'pending' | 'queued' | 'running' | 'completed' | 'failed' | 'rolled_back'
  config: Record<string, any>
  schedule_type?: 'immediate' | 'scheduled'
  schedule_value?: string // Cron expression or ISO timestamp
  current_version?: string
  target_version?: string
  created_at: string
  updated_at: string
}

export interface DeploymentExecution {
  id: string
  deployment_id: string
  status: 'pending' | 'queued' | 'running' | 'completed' | 'failed'
  dry_run: boolean
  started_at?: string
  completed_at?: string
  duration_seconds?: number
  current_version?: string
  target_version?: string
  output?: string
  error?: string
  rollback_available: boolean
}

export interface DeploymentHistory {
  id: string
  deployment_id: string
  deployment_name: string
  server_id: string
  server_hostname?: string
  status: string
  dry_run: boolean
  started_at: string
  completed_at?: string
  duration_seconds?: number
  current_version?: string
  target_version?: string
  output?: string
  error?: string
}

export interface CreateDeploymentRequest {
  server_id: string
  name: string
  description?: string
  deployment_type: 'manual' | 'scheduled' | 'git' | 'docker'
  config: Record<string, any>
  schedule_type?: 'immediate' | 'scheduled'
  schedule_value?: string
}

export interface UpdateDeploymentRequest {
  name?: string
  description?: string
  config?: Record<string, any>
  schedule_type?: 'immediate' | 'scheduled'
  schedule_value?: string
}

// ============================================
// Dashboard Types
// ============================================

export interface DashboardStats {
  servers_total: number
  servers_online: number
  servers_offline: number
  organizations_total: number
  alerts_active: number
  alerts_critical: number
  commands_today: number
}

export interface ServerHealthOverview {
  server_id: string
  server_name: string
  status: 'online' | 'offline' | 'error' | 'connecting'
  cpu_usage: number
  memory_usage: number
  disk_usage: number
  uptime: number
  last_seen: string
}

export interface RecentAlert {
  id: string
  server_name: string
  severity: 'info' | 'warning' | 'critical'
  title: string
  message: string
  created_at: string
}

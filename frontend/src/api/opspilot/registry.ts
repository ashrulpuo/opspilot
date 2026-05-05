import request from './client'

export interface Domain {
  id: string
  org_id: string
  server_id?: string
  name: string
  registrar?: string
  registered_at?: string
  expires_at?: string
  auto_renew: boolean
  nameservers?: string
  notes?: string
  tags?: string
  created_at: string
}

export interface SslCert {
  id: string
  org_id: string
  domain_id?: string
  domain_name: string
  common_name?: string
  issuer?: string
  issued_at?: string
  expires_at?: string
  fingerprint?: string
  auto_renew: boolean
  provider?: string
  notes?: string
  created_at: string
}

export interface DbService {
  id: string
  org_id: string
  server_id?: string
  name: string
  db_type: string
  host: string
  port?: number
  database_name?: string
  username?: string
  has_password: boolean
  environment: string
  ssl_enabled: boolean
  notes?: string
  tags?: string
  created_at: string
}

export interface Credential {
  id: string
  org_id: string
  server_id?: string
  name: string
  credential_type: string
  url?: string
  username?: string
  has_secret: boolean
  environment: string
  notes?: string
  tags?: string
  created_at: string
}

export interface AuditLog {
  id: string
  user_id?: string
  asset_type: string
  asset_id: string
  action: string
  ip_address?: string
  created_at: string
}

export const RegistryAPI = {
  listDomains: (): Promise<Domain[]> => request.get('/registry/domains'),
  createDomain: (data: Record<string, unknown>): Promise<Domain> => request.post('/registry/domains', data),
  updateDomain: (id: string, data: Record<string, unknown>): Promise<Domain> =>
    request.put(`/registry/domains/${id}`, data),
  deleteDomain: (id: string): Promise<void> => request.delete(`/registry/domains/${id}`),

  listSslCerts: (): Promise<SslCert[]> => request.get('/registry/ssl-certs'),
  createSslCert: (data: Record<string, unknown>): Promise<SslCert> => request.post('/registry/ssl-certs', data),
  updateSslCert: (id: string, data: Record<string, unknown>): Promise<SslCert> =>
    request.put(`/registry/ssl-certs/${id}`, data),
  deleteSslCert: (id: string): Promise<void> => request.delete(`/registry/ssl-certs/${id}`),

  listDatabases: (): Promise<DbService[]> => request.get('/registry/databases'),
  createDatabase: (data: Record<string, unknown>): Promise<DbService> => request.post('/registry/databases', data),
  updateDatabase: (id: string, data: Record<string, unknown>): Promise<DbService> =>
    request.put(`/registry/databases/${id}`, data),
  deleteDatabase: (id: string): Promise<void> => request.delete(`/registry/databases/${id}`),
  revealDbPassword: (id: string): Promise<{ value: string }> => request.get(`/registry/databases/${id}/reveal`),

  listCredentials: (): Promise<Credential[]> => request.get('/registry/credentials'),
  createCredential: (data: Record<string, unknown>): Promise<Credential> => request.post('/registry/credentials', data),
  updateCredential: (id: string, data: Record<string, unknown>): Promise<Credential> =>
    request.put(`/registry/credentials/${id}`, data),
  deleteCredential: (id: string): Promise<void> => request.delete(`/registry/credentials/${id}`),
  revealCredentialSecret: (id: string): Promise<{ value: string }> => request.get(`/registry/credentials/${id}/reveal`),

  getAuditLog: (asset_id?: string): Promise<AuditLog[]> =>
    request.get('/registry/audit-log', { params: asset_id ? { asset_id } : {} }),
  search: (q: string): Promise<{ type: string; id: string; name: string; subtitle: string }[]> =>
    request.get('/registry/search', { params: { q } }),
}

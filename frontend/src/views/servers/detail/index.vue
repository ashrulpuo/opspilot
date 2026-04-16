<template>
  <div class="server-detail-container">
    <!-- Loading state -->
    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="10" animated />
    </div>

    <!-- Server content -->
    <div v-else-if="server" class="server-content">
      <!-- Page Header -->
      <div class="page-header">
        <div class="header-left">
          <el-button link @click="$router.push('/servers')" class="back-button">
            <el-icon><ArrowLeft /></el-icon>
            Back to Servers
          </el-button>
          <div class="server-info">
            <div class="server-title-row">
              <h1 class="server-title">{{ server.hostname }}</h1>
              <el-tag :type="getStatusType(server.status)" size="large">
                {{ server.status }}
              </el-tag>
            </div>
            <p class="server-subtitle">{{ server.ip_address }}</p>
          </div>
        </div>
        <div class="header-actions">
          <el-button type="primary" @click="handleSSH">
            <el-icon><Monitor /></el-icon>
            SSH Terminal
          </el-button>
          <el-button @click="showEditDialog = true">
            <el-icon><Edit /></el-icon>
            Edit
          </el-button>
          <el-popconfirm title="Are you sure you want to delete this server?" @confirm="handleDelete">
            <template #reference>
              <el-button type="danger" plain>
                <el-icon><Delete /></el-icon>
                Delete
              </el-button>
            </template>
          </el-popconfirm>
        </div>
      </div>

      <!-- Content Tabs -->
      <el-tabs v-model="activeTab" class="server-tabs">
        <!-- Overview Tab -->
        <el-tab-pane label="Overview" name="overview">
          <div class="overview-section">
            <div class="info-grid">
              <div class="info-card hc-card">
                <h3 class="info-title">Server Information</h3>
                <div class="info-list">
                  <div class="info-item">
                    <span class="info-label">Hostname</span>
                    <span class="info-value">{{ server.hostname }}</span>
                  </div>
                  <div class="info-item">
                    <span class="info-label">IP Address</span>
                    <span class="info-value">{{ server.ip_address }}</span>
                  </div>
                  <div class="info-item">
                    <span class="info-label">OS Type</span>
                    <el-tag :type="getOSType(server.os_type)" size="small">
                      {{ server.os_type.toUpperCase() }}
                    </el-tag>
                  </div>
                  <div class="info-item">
                    <span class="info-label">Domain</span>
                    <span class="info-value">{{ server.domain_name || '-' }}</span>
                  </div>
                  <div class="info-item">
                    <span class="info-label">Web Server</span>
                    <el-tag v-if="server.web_server_type" type="info" size="small">
                      {{ server.web_server_type }}
                    </el-tag>
                    <span v-else class="empty-text">-</span>
                  </div>
                  <div class="info-item">
                    <span class="info-label">Status</span>
                    <el-tag :type="getStatusType(server.status)" size="small">
                      {{ server.status }}
                    </el-tag>
                  </div>
                  <div class="info-item">
                    <span class="info-label">Created</span>
                    <span class="info-value">{{ formatDate(server.created_at) }}</span>
                  </div>
                  <div class="info-item">
                    <span class="info-label">Last Seen</span>
                    <span class="info-value">{{ formatDate(server.updated_at) }}</span>
                  </div>
                </div>
              </div>

              <div class="info-card hc-card">
                <h3 class="info-title">System Resources</h3>
                <div class="metrics-placeholder">
                  <el-empty description="Metrics will be available when server comes online" />
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <!-- SSH Terminal Tab -->
        <el-tab-pane label="SSH Terminal" name="ssh">
          <div class="ssh-section">
            <div v-if="!sshConnected" class="ssh-connect-section">
              <div class="ssh-placeholder">
                <el-icon class="ssh-icon"><Monitor /></el-icon>
                <h3>SSH Terminal</h3>
                <p>Connect to your server via SSH terminal</p>
                <el-button type="primary" @click="handleSSHConnect" :loading="sshConnecting">
                  <el-icon><VideoPlay /></el-icon>
                  {{ sshConnecting ? 'Connecting...' : 'Connect to Server' }}
                </el-button>
              </div>
            </div>

            <div v-else class="ssh-terminal-container">
              <div class="ssh-terminal-toolbar">
                <el-button link type="primary" @click="handleSSHDisconnect">
                  <el-icon><VideoPause /></el-icon>
                  Disconnect
                </el-button>
                <span class="session-info">Connected to {{ server.hostname }}</span>
              </div>
              <!-- xterm.js terminal container -->
              <div ref="terminalRef" class="xterm-terminal"></div>
            </div>
          </div>
        </el-tab-pane>

        <!-- Alerts Tab -->
        <el-tab-pane label="Alerts" name="alerts">
          <div class="alerts-section">
            <el-empty description="No alerts for this server" />
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- Not found state -->
    <div v-else class="not-found-state">
      <el-empty description="Server not found">
        <el-button type="primary" @click="$router.push('/servers')"> Back to Servers </el-button>
      </el-empty>
    </div>

    <!-- Edit Server Dialog -->
    <el-dialog v-model="showEditDialog" title="Edit Server" width="500px" :close-on-click-modal="false">
      <el-form ref="editFormRef" :model="editForm" label-width="120px">
        <el-form-item label="Hostname">
          <el-input v-model="editForm.hostname" />
        </el-form-item>

        <el-form-item label="IP Address">
          <el-input v-model="editForm.ip_address" />
        </el-form-item>

        <el-form-item label="Domain Name">
          <el-input v-model="editForm.domain_name" placeholder="Optional" />
        </el-form-item>

        <el-form-item label="Web Server">
          <el-select v-model="editForm.web_server_type" placeholder="Optional" style="width: 100%" clearable>
            <el-option label="Nginx" value="nginx" />
            <el-option label="Apache" value="apache" />
            <el-option label="Caddy" value="caddy" />
            <el-option label="IIS" value="iis" />
            <el-option label="None" value="none" />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showEditDialog = false">Cancel</el-button>
        <el-button type="primary" @click="handleEditSave">Save Changes</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Monitor, Edit, Delete, VideoPlay, VideoPause } from '@element-plus/icons-vue'
import { ServersAPI } from '@/api/opspilot/servers'
import { SSHTerminalAPI } from '@/api/opspilot/commands'

const route = useRoute()
const router = useRouter()

const serverId = route.params.id as string
const activeTab = ref((route.query.tab as string) || 'overview')

const loading = ref(true)
const server = ref<any>(null)
const showEditDialog = ref(false)
const editFormRef = ref()

const sshConnecting = ref(false)
const sshConnected = ref(false)
const sshSessionId = ref<string>()
const terminalRef = ref<HTMLDivElement>()
const ws = ref<WebSocket>()
const xterm = ref<any>()

const editForm = reactive({
  hostname: '',
  ip_address: '',
  domain_name: '',
  web_server_type: '',
})

const getOSType = (osType: string) => {
  switch (osType.toLowerCase()) {
    case 'linux':
      return 'primary'
    case 'macos':
      return 'info'
    case 'windows':
      return 'warning'
    default:
      return 'info'
  }
}

const getStatusType = (status: string) => {
  switch (status) {
    case 'online':
      return 'success'
    case 'offline':
      return 'info'
    case 'error':
      return 'danger'
    case 'connecting':
      return 'warning'
    default:
      return 'info'
  }
}

const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const handleSSH = () => {
  activeTab.value = 'ssh'
}

const handleSSHConnect = async () => {
  try {
    sshConnecting.value = true

    // Create SSH session
    const session = await SSHTerminalAPI.createSession(serverId)
    sshSessionId.value = session.session_id

    ElMessage.success('SSH session created')

    // Initialize xterm.js
    // TODO: Install xterm.js: npm install xterm xterm-addon-fit xterm-addon-web-links
    // const { Terminal } = await import('xterm');
    // const { FitAddon } = await import('xterm-addon-fit');

    // const term = new Terminal({
    //   cursorBlink: true,
    //   theme: {
    //     background: '#000000',
    //     foreground: '#ffffff',
    //   },
    // });

    // const fitAddon = new FitAddon();
    // term.loadAddon(fitAddon);

    // if (terminalRef.value) {
    //   term.open(terminalRef.value);
    //   fitAddon.fit();
    // }

    // Connect to WebSocket
    ws.value = SSHTerminalAPI.connect(session.session_id)

    ws.value.onopen = () => {
      console.log('SSH WebSocket connected')
      sshConnected.value = true
      sshConnecting.value = false

      // Send resize event
      if (terminalRef.value) {
        const cols = Math.floor(terminalRef.value.offsetWidth / 9) // Approximate character width
        const rows = Math.floor(terminalRef.value.offsetHeight / 18) // Approximate line height
        ws.value?.send(JSON.stringify({ type: 'resize', rows, cols }))
      }
    }

    ws.value.onmessage = event => {
      const message = JSON.parse(event.data)
      console.log('SSH WebSocket message:', message)

      // TODO: Handle message types
      // if (message.type === 'output') {
      //   term.write(message.output);
      // } else if (message.type === 'welcome') {
      //   term.write(`\r\n${message.message}\r\n`);
      //   term.write(`root@${server.value.hostname}:# `);
      // } else if (message.type === 'error') {
      //   term.write(`\r\n${message.message}\r\n`);
      // }
    }

    ws.value.onclose = () => {
      console.log('SSH WebSocket closed')
      sshConnected.value = false
    }

    ws.value.onerror = error => {
      console.error('SSH WebSocket error:', error)
      ElMessage.error('SSH connection error')
      sshConnected.value = false
      sshConnecting.value = false
    }
  } catch (error: any) {
    console.error('SSH connect error:', error)
    ElMessage.error(error.message || 'Failed to connect to SSH')
    sshConnecting.value = false
  }
}

const handleSSHDisconnect = async () => {
  if (sshSessionId.value) {
    try {
      await SSHTerminalAPI.terminateSession(sshSessionId.value)
      ElMessage.success('SSH session terminated')
      sshConnected.value = false
      sshSessionId.value = undefined

      // Close WebSocket
      if (ws.value) {
        ws.value.close()
        ws.value = undefined
      }
    } catch (error: any) {
      console.error('SSH disconnect error:', error)
      ElMessage.error(error.message || 'Failed to disconnect SSH')
    }
  }
}

const handleEditSave = async () => {
  try {
    const updateData: any = {}
    if (editForm.hostname) updateData.hostname = editForm.hostname
    if (editForm.ip_address) updateData.ip_address = editForm.ip_address
    if (editForm.domain_name) updateData.domain_name = editForm.domain_name
    if (editForm.web_server_type) updateData.web_server_type = editForm.web_server_type

    await ServersAPI.update(serverId, updateData)
    ElMessage.success('Server updated successfully')
    showEditDialog.value = false

    // Reload server data
    await loadServer()
  } catch (error: any) {
    console.error('Update server error:', error)
    ElMessage.error(error.message || 'Failed to update server')
  }
}

const handleDelete = async () => {
  try {
    await ServersAPI.delete(serverId)
    ElMessage.success('Server deleted successfully')
    router.push('/servers')
  } catch (error: any) {
    console.error('Delete server error:', error)
    ElMessage.error(error.message || 'Failed to delete server')
  }
}

const loadServer = async () => {
  try {
    loading.value = true
    server.value = await ServersAPI.get(serverId)

    // Populate edit form
    editForm.hostname = server.value.hostname
    editForm.ip_address = server.value.ip_address
    editForm.domain_name = server.value.domain_name || ''
    editForm.web_server_type = server.value.web_server_type || ''
  } catch (error: any) {
    console.error('Load server error:', error)
    ElMessage.error(error.message || 'Failed to load server')
    server.value = null
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadServer()

  // Handle window resize for terminal
  window.addEventListener('resize', () => {
    if (ws.value && terminalRef.value) {
      const cols = Math.floor(terminalRef.value.offsetWidth / 9)
      const rows = Math.floor(terminalRef.value.offsetHeight / 18)
      ws.value.send(JSON.stringify({ type: 'resize', rows, cols }))
    }
  })
})

onUnmounted(() => {
  // Cleanup WebSocket and SSH session
  if (ws.value) {
    ws.value.close()
  }
  if (sshSessionId.value) {
    handleSSHDisconnect()
  }
})
</script>

<style scoped lang="scss">
.server-detail-container {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;

  .back-button {
    margin-bottom: 16px;
    font-size: 0.875rem;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 0;
  }

  .server-info {
    .server-title-row {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 8px;

      .server-title {
        font-family:
          system-ui,
          -apple-system,
          BlinkMacSystemFont,
          'Segoe UI',
          sans-serif;
        font-size: 2rem;
        font-weight: 700;
        color: #000000;
        line-height: 1.2;
        margin: 0;
      }
    }

    .server-subtitle {
      font-family:
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        'Segoe UI',
        sans-serif;
      font-size: 1rem;
      font-weight: 400;
      color: #656a76;
      line-height: 1.5;
      margin: 0;
    }
  }

  .header-actions {
    display: flex;
    gap: 12px;
  }
}

html.dark .page-header .server-info {
  .server-title-row .server-title {
    color: #ffffff;
  }

  .server-subtitle {
    color: #d5d7db;
  }
}

.server-tabs {
  background: transparent;
}

.overview-section {
  .info-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 24px;
  }

  .info-card {
    padding: 24px;

    .info-title {
      font-family:
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        'Segoe UI',
        sans-serif;
      font-size: 1.125rem;
      font-weight: 600;
      color: #000000;
      line-height: 1.3;
      margin: 0 0 20px 0;
    }

    .info-list {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .info-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 16px;
      border-bottom: 1px solid #d5d7db;

      &:last-child {
        border-bottom: none;
        padding-bottom: 0;
      }

      .info-label {
        font-family:
          system-ui,
          -apple-system,
          BlinkMacSystemFont,
          'Segoe UI',
          sans-serif;
        font-size: 0.875rem;
        font-weight: 500;
        color: #656a76;
        line-height: 1.4;
      }

      .info-value {
        font-family:
          system-ui,
          -apple-system,
          BlinkMacSystemFont,
          'Segoe UI',
          sans-serif;
        font-size: 0.875rem;
        font-weight: 400;
        color: #000000;
        line-height: 1.4;
      }

      .empty-text {
        font-family:
          system-ui,
          -apple-system,
          BlinkMacSystemFont,
          'Segoe UI',
          sans-serif;
        font-size: 0.875rem;
        font-weight: 400;
        color: #656a76;
        line-height: 1.4;
      }
    }
  }
}

html.dark .overview-section .info-card {
  .info-title {
    color: #ffffff;
  }

  .info-item {
    border-bottom-color: rgba(178, 182, 189, 0.4);

    .info-label {
      color: #b2b6bd;
    }

    .info-value {
      color: #ffffff;
    }

    .empty-text {
      color: #656a76;
    }
  }
}

.ssh-section {
  .ssh-connect-section {
    .ssh-placeholder {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 80px 24px;
      text-align: center;

      .ssh-icon {
        font-size: 64px;
        color: #15181e;
        margin-bottom: 24px;
      }

      h3 {
        font-family:
          system-ui,
          -apple-system,
          BlinkMacSystemFont,
          'Segoe UI',
          sans-serif;
        font-size: 1.25rem;
        font-weight: 600;
        color: #000000;
        line-height: 1.3;
        margin: 0 0 8px 0;
      }

      p {
        font-family:
          system-ui,
          -apple-system,
          BlinkMacSystemFont,
          'Segoe UI',
          sans-serif;
        font-size: 0.9375rem;
        font-weight: 400;
        color: #656a76;
        line-height: 1.5;
        margin: 0 0 24px 0;
      }
    }
  }

  .ssh-terminal-container {
    background: #000000;
    border-radius: 8px;
    overflow: hidden;

    .ssh-terminal-toolbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 16px;
      background: rgba(255, 255, 255, 0.1);
      border-bottom: 1px solid rgba(255, 255, 255, 0.2);

      .session-info {
        font-family: monospace;
        font-size: 0.875rem;
        color: #ffffff;
      }
    }

    .xterm-terminal {
      padding: 16px;
      height: calc(100vh - 300px);
      min-height: 400px;
    }
  }
}

html.dark .ssh-section .ssh-connect-section .ssh-placeholder {
  .ssh-icon {
    color: #ffffff;
  }

  h3 {
    color: #ffffff;
  }

  p {
    color: #d5d7db;
  }
}

.alerts-section,
.metrics-placeholder {
  padding: 60px 24px;
}

.loading-state,
.not-found-state {
  padding: 60px 24px;
}

// Responsive design
@media (max-width: 768px) {
  .server-detail-container {
    padding: 16px;
  }

  .page-header {
    .server-info .server-title-row {
      flex-direction: column;
      align-items: flex-start;
      gap: 8px;

      .server-title {
        font-size: 1.5rem;
      }
    }

    .header-actions {
      width: 100%;
      display: flex;
      flex-wrap: wrap;
      gap: 8px;

      .el-button {
        flex: 1;
        min-width: 120px;
      }
    }
  }

  .overview-section .info-grid {
    grid-template-columns: 1fr;
  }

  .ssh-section .ssh-terminal-container .xterm-terminal {
    height: calc(100vh - 250px);
  }
}
</style>

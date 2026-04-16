<template>
  <div class="ssh-terminal">
    <div class="terminal-header">
      <el-space>
        <el-tag type="success">Connected</el-tag>
        <span class="server-info">{{ server.hostname }}</span>
        <el-button size="small" @click="disconnect">Disconnect</el-button>
      </el-space>
    </div>
    <div ref="terminalContainer" class="terminal-container"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { Terminal } from 'xterm'
import { FitAddon } from 'xterm-addon-fit'
import { WebLinksAddon } from 'xterm-addon-web-links'
import 'xterm/css/xterm.css'

interface Props {
  serverId: string
  hostname: string
}

const props = defineProps<Props>()

const emit = defineEmits(['disconnect'])

const terminalContainer = ref<HTMLElement>()
let terminal: Terminal | null = null
let fitAddon: FitAddon | null = null
let socket: WebSocket | null = null

onMounted(() => {
  initTerminal()
})

onBeforeUnmount(() => {
  cleanup()
})

function initTerminal() {
  if (!terminalContainer.value) return

  // Initialize xterm.js terminal
  terminal = new Terminal({
    cursorBlink: true,
    fontSize: 14,
    fontFamily: 'Menlo, Monaco, "Courier New", monospace',
    theme: {
      background: '#1e1e1e',
      foreground: '#d4d4d4',
      cursor: '#ffffff',
      selection: '#3a3d41',
    },
  })

  // Add addons
  fitAddon = new FitAddon()
  const webLinksAddon = new WebLinksAddon()

  terminal.loadAddon(fitAddon)
  terminal.loadAddon(webLinksAddon)

  // Mount terminal to container
  terminal.open(terminalContainer.value)
  fitAddon!.fit()

  // Connect to WebSocket
  connectWebSocket()

  // Handle terminal resize
  window.addEventListener('resize', handleResize)

  // Handle user input
  terminal.onData(data => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(
        JSON.stringify({
          type: 'input',
          data: data,
        })
      )
    }
  })
}

function connectWebSocket() {
  const wsUrl = `ws://localhost:8000/api/v1/sessions/${props.serverId}/ssh`
  socket = new WebSocket(wsUrl)

  socket.onopen = () => {
    if (terminal) {
      terminal.writeln('\x1b[32mConnected to ' + props.hostname + '\x1b[0m')
      terminal.writeln('\r\n')
    }
  }

  socket.onmessage = event => {
    const message = JSON.parse(event.data)

    if (message.type === 'output' && terminal) {
      terminal.write(message.data)
    } else if (message.type === 'error' && terminal) {
      terminal.writeln('\x1b[31mError: ' + message.data + '\x1b[0m')
    }
  }

  socket.onerror = error => {
    console.error('WebSocket error:', error)
    if (terminal) {
      terminal.writeln('\x1b[31mConnection error\x1b[0m')
    }
  }

  socket.onclose = () => {
    if (terminal) {
      terminal.writeln('\x1b[33mConnection closed\x1b[0m')
    }
  }
}

function handleResize() {
  if (fitAddon && terminal) {
    fitAddon.fit()

    // Send new terminal size to server
    if (socket && socket.readyState === WebSocket.OPEN) {
      const dims = { cols: terminal.cols, rows: terminal.rows }
      socket.send(
        JSON.stringify({
          type: 'resize',
          cols: dims.cols,
          rows: dims.rows,
        })
      )
    }
  }
}

function disconnect() {
  cleanup()
  emit('disconnect')
}

function cleanup() {
  if (socket) {
    socket.close()
    socket = null
  }

  if (terminal) {
    terminal.dispose()
    terminal = null
  }

  if (fitAddon) {
    fitAddon = null
  }

  window.removeEventListener('resize', handleResize)
}
</script>

<style scoped>
.ssh-terminal {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #1e1e1e;
}

.terminal-header {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: #252526;
  border-bottom: 1px solid #333;
}

.server-info {
  color: #d4d4d4;
  font-size: 14px;
  margin: 0 12px;
}

.terminal-container {
  flex: 1;
  padding: 8px;
  overflow: hidden;
}
</style>

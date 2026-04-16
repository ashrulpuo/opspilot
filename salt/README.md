# OpsPilot SaltStack

SaltStack states and modules for OpsPilot server automation.

## Overview

This repository contains SaltStack configurations for managing servers through OpsPilot. It includes states for system setup, monitoring, logging, and remote execution.

## Structure

```
opspilot-salt/
├── pillar/                 # Pillar data (secrets, configuration)
│   ├── top.sls            # Top file for pillar assignment
│   ├── base/              # Base pillar data
│   └── environments/      # Environment-specific pillars (dev, prod)
├── salt/                   # Salt states
│   ├── top.sls            # Top file for state assignment
│   ├── base/              # Base states
│   │   ├── opspilot/      # OpsPilot-specific states
│   │   ├── monitoring/    # Monitoring and metrics
│   │   ├── logging/       # Logging configuration
│   │   └── security/      # Security hardening
│   └── _modules/          # Custom Salt modules
└── formulas/               # Third-party Salt formulas
```

## Quick Start

### Salt Master Setup

```bash
# Install Salt Master
apt-get install salt-master

# Copy ops states to Salt master
cp -r salt/* /srv/salt/
cp -r pillar/* /srv/pillar/

# Restart Salt Master
systemctl restart salt-master
```

### Minion Setup

```bash
# Install Salt Minion
apt-get install salt-minion

# Configure minion ID (use server hostname)
echo "opspilot-minion-$(hostname)" > /etc/salt/minion_id

# Configure master
echo "master: salt-master.example.com" > /etc/salt/minion.d/master.conf

# Start minion
systemctl start salt-minion

# Accept key on master
salt-key -a opspilot-minion-$(hostname)
```

### Apply States

```bash
# Apply base state to all minions
salt '*' state.apply

# Apply specific state
salt 'minion-id' state.apply opspilot.setup

# Apply monitoring state
salt 'minion-id' state.apply monitoring.prometheus
```

## States

### OpsPilot Base State
- Installs required dependencies
- Configures OpsPilot agent
- Sets up communication with OpsPilot API

### Monitoring
- Installs and configures Prometheus node_exporter
- Configures metrics collection intervals
- Sets up alert rules

### Logging
- Configures centralized logging
- Ships logs to OpsPilot backend
- Sets up log rotation

### Security
- System hardening
- SSH configuration
- Firewall rules

## Custom Modules

### opspilot.py
Custom Salt module for OpsPilot-specific operations:
- Server registration
- Metrics retrieval
- Log streaming
- Command execution with output capture

## Pillar Data

Sensitive data (API keys, passwords, etc.) should be stored in pillar and encrypted with GPG.

```bash
# Encrypt pillar file
gpg --encrypt --recipient user@example.com pillar/secret.sls

# Decrypt on minion (automatic with GPG renderer)
```

## Testing

```bash
# Test state syntax
salt '*' state.show_highstate

# Apply in test mode (no changes)
salt '*' state.test

# Apply specific state in test mode
salt 'minion-id' state.test opspilot.setup
```

## Best Practices

1. **State Reusability**: Write reusable states with parameters
2. **Idempotency**: Ensure states can be applied multiple times safely
3. **Testing**: Test states in dev environment before production
4. **Documentation**: Document state purpose and requirements
5. **Security**: Keep secrets in encrypted pillar

## Troubleshooting

### Minion Not Responding

```bash
# Check minion status
salt '*' test.ping

# Check minion logs
tail -f /var/log/salt/minion

# Restart minion
systemctl restart salt-minion
```

### State Execution Errors

```bash
# View detailed state output
salt 'minion-id' state.apply -l debug

# Check state documentation
salt '*' sys.doc state.apply
```

## License

MIT

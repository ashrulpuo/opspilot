# OpsPilot Security State
# System hardening and security configuration

{% set security_config = salt['pillar'].get('security', {}) %}

# Configure firewall rules
firewall-configuration:
  file.managed:
    - name: /etc/ufw/allowed.rules
    - contents: |
      # OpsPilot allowed ports
      * allow 22/tcp   # SSH
      * allow 4505/tcp # Salt master
      * allow 4506/tcp # Salt minion
      * allow 8000/tcp # Salt API
      * allow 9000/tcp # OpsPilot backend
      * deny all
    - user: root
    - mode: '0640'
    - require:
      - pkg: ufw-installed

# Install and configure fail2ban
fail2ban-configuration:
  file.managed:
    - name: /etc/fail2ban/jail.local
    - contents: |
      [DEFAULT]
      bantime = 3600
      findtime = 600
      maxretry = 5
      destemail = {{ security_config.get('alert_email', 'admin@example.com') }}
      
      [sshd]
      enabled = true
      port = 22
      logpath = /var/log/auth.log
      maxretry = 3
      banaction = iptables-multiport
      banaction_allports = 22,4505,4506
    - user: root
    - mode: '0644'

fail2ban-service:
  service.running:
    - name: fail2ban
    - enable: True
    - require:
      - file: fail2ban-configuration
      - pkg: fail2ban-pkgs

# SSH hardening
ssh-configuration:
  file.managed:
    - name: /etc/ssh/sshd_config.d/opspilot-hardening.conf
    - contents: |
      # SSH hardening
      Protocol 2
      PermitRootLogin {{ security_config.get('allow_root_ssh', 'no') }}
      PasswordAuthentication no
      PubkeyAuthentication yes
      MaxAuthTries 3
      ClientAliveInterval 300
      ClientAliveCountMax 2
      X11Forwarding no
      AllowTcpForwarding no
      AllowAgentForwarding no
      GatewayPorts no
    - user: root
    - mode: '0644'
    - require:
      - pkg: ssh-server-pkgs

# Disable unused services
disable-unused-services:
  service.dead:
    - names:
      - telnet
      - rsh
      - rlogin
      - rexec
    - enable: False

# System hardening parameters
sysctl-hardening:
  sysctl.present:
    - name: kernel.randomize_va_space
    - value: 2
    - config: /etc/sysctl.conf
  sysctl.present:
    - name: net.ipv4.ip_forward
    - value: 0
    - config: /etc/sysctl.conf
  sysctl.present:
    - name: net.ipv4.conf.all.send_redirects
    - value: 0
    - config: /etc/sysctl.conf
  sysctl.present:
    - name: net.ipv4.conf.all.accept_source_route
    - value: 0
    - config: /etc/sysctl.conf
  sysctl.present:
    - name: kernel.kptr_restrict
    - value: 2
    - config: /etc/sysctl.conf

# Configure automatic security updates
security-updates:
  file.managed:
    - name: /etc/apt/apt.conf.d/50unattended-upgrades
    - contents: |
      Unattended-Upgrade::AutoFixInterruptedDpkg "true";
      Unattended-Upgrade::Remove-Unused-Dependencies "true";
      Unattended-Upgrade::Automatic-Reboot "false";
      Unattended-Upgrade::MinimalSteps "true";
    - user: root
    - mode: '0644'

# Install security packages
security-packages:
  pkg.installed:
    - names:
      - ufw
      - fail2ban
      - auditd
      - rkhunter
      - aide
    - refresh: True

#!/bin/bash
# Auto-install Salt Minion on remote servers
# Usage: ./install-salt-minion.sh <server_ip> <ssh_user> <ssh_password_or_key> <minion_id> <master_ip>

set -e

# Check arguments
if [ $# -lt 4 ]; then
    echo "Usage: $0 <server_ip> <ssh_user> <ssh_password_or_key> <minion_id> [master_ip]"
    echo ""
    echo "Arguments:"
    echo "  server_ip           - IP address of the target server"
    echo "  ssh_user            - SSH username (e.g., root)"
    echo "  ssh_password_or_key - SSH password or path to private key file"
    echo "  minion_id           - Unique minion ID (e.g., server1.example.com)"
    echo "  master_ip           - Salt master IP (default: current server's IP)"
    echo ""
    echo "Examples:"
    echo "  $0 192.168.1.100 root mypassword webserver1 192.168.1.10"
    echo "  $0 192.168.1.100 root ~/.ssh/id_ed25519 webserver1"
    exit 1
fi

SERVER_IP="$1"
SSH_USER="$2"
SSH_CREDENTIAL="$3"
MINION_ID="$4"
MASTER_IP="${5:-$(hostname -I | awk '{print $1}')}"

# Detect SSH authentication method
SSH_AUTH=""
if [ -f "$SSH_CREDENTIAL" ]; then
    SSH_AUTH="-i $SSH_CREDENTIAL"
    SSH_CMD="ssh -i $SSH_CREDENTIAL -o StrictHostKeyChecking=no"
else
    SSH_CMD="sshpass -p '$SSH_CREDENTIAL' ssh -o StrictHostKeyChecking=no"
fi

echo "=========================================="
echo "Salt Minion Auto-Install Script"
echo "=========================================="
echo "Target Server: $SERVER_IP"
echo "SSH User: $SSH_USER"
echo "Minion ID: $MINION_ID"
echo "Salt Master: $MASTER_IP"
echo "=========================================="

# Detect OS
echo "Detecting operating system..."
OS=$($SSH_CMD ${SSH_USER}@${SERVER_IP} "cat /etc/os-release | grep '^ID=' | cut -d= -f2 | tr -d '\"'")

echo "Detected OS: $OS"

# Install Salt Minion based on OS
case "$OS" in
    ubuntu|debian)
        echo "Installing Salt Minion on Debian/Ubuntu..."
        $SSH_CMD ${SSH_USER}@${SERVER_IP} "
            sudo apt-get update
            sudo apt-get install -y curl gnupg lsb-release
            sudo curl -fsSL https://repo.saltproject.io/salt/py3/ubuntu/$(lsb_release -sr)/amd64/latest/salt-archive-keyring.gpg | sudo tee /usr/share/keyrings/salt-archive-keyring.gpg > /dev/null
            echo 'deb [signed-by=/usr/share/keyrings/salt-archive-keyring.gpg] https://repo.saltproject.io/salt/py3/ubuntu/$(lsb_release -sr)/amd64/latest $(lsb_release -sc) main' | sudo tee /etc/apt/sources.list.d/salt.list
            sudo apt-get update
            sudo apt-get install -y salt-minion
        "
        ;;

    rhel|centos|fedora)
        echo "Installing Salt Minion on RHEL/CentOS/Fedora..."
        $SSH_CMD ${SSH_USER}@${SERVER_IP} "
            sudo yum install -y https://repo.saltproject.io/salt/py3/redhat/$(rpm -E %rhel)/x86_64/latest/salt-repo-$(rpm -E %rhel).el$(rpm -E %rhel).x86_64.rpm || \
            sudo dnf install -y https://repo.saltproject.io/salt/py3/fedora/$(rpm -E %fedora)/x86_64/latest/salt-repo-$(rpm -E %fedora).fc$(rpm -E %fedora).x86_64.rpm
            sudo yum install -y salt-minion || sudo dnf install -y salt-minion
        "
        ;;

    *)
        echo "Unsupported OS: $OS"
        echo "Please install Salt Minion manually: https://docs.saltproject.io/salt/install/en/latest/"
        exit 1
        ;;
esac

# Configure Salt Minion
echo "Configuring Salt Minion..."
$SSH_CMD ${SSH_USER}@${SERVER_IP} "
    sudo sed -i \"s/^#master: .*$/master: ${MASTER_IP}/\" /etc/salt/minion
    sudo sed -i \"s/^#id: .*$/id: ${MINION_ID}/\" /etc/salt/minion
    echo 'master: ${MASTER_IP}' | sudo tee -a /etc/salt/minion
    echo 'id: ${MINION_ID}' | sudo tee -a /etc/salt/minion
"

# Start Salt Minion
echo "Starting Salt Minion..."
$SSH_CMD ${SSH_USER}@${SERVER_IP} "
    sudo systemctl enable salt-minion
    sudo systemctl restart salt-minion
"

# Verify minion is running
echo "Verifying Salt Minion is running..."
sleep 5
MINION_STATUS=$($SSH_CMD ${SSH_USER}@${SERVER_IP} "sudo systemctl is-active salt-minion")

if [ "$MINION_STATUS" = "active" ]; then
    echo "✓ Salt Minion is running on ${SERVER_IP}"
else
    echo "✗ Salt Minion failed to start on ${SERVER_IP}"
    exit 1
fi

echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. On Salt master, accept the minion key:"
echo "   sudo salt-key -A"
echo ""
echo "2. Verify minion connection:"
echo "   sudo salt '${MINION_ID}' test.ping"
echo ""
echo "3. Register minion in OpsPilot database"
echo "=========================================="

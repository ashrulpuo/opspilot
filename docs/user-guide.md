# SaltStack Data Collection - User Guide

## Overview

The SaltStack Data Collection feature provides real-time monitoring, management, and observability for servers managed by OpsPilot. This guide covers all features and how to use them.

## Table of Contents

- [Getting Started](#getting-started)
- [Server Management](#server-management)
- [Real-Time Metrics](#real-time-metrics)
- [Service Management](#service-management)
- [Process Monitoring](#process-monitoring)
- [Package Management](#package-management)
- [Log Aggregation](#log-aggregation)
- [Alert System](#alert-system)
- [Salt Minion Information](#salt-minion-information)

---

## Getting Started

### Prerequisites

- **Salt Minion:** Each server must have Salt minion installed and configured
- **Network Access:** Minion must be able to connect to the OpsPilot backend
- **Permissions:** User must have appropriate permissions (DevOps or Admin role)

### Adding a Server

1. Navigate to **Servers** → **Add Server**
2. Enter server details:
   - **Name:** Friendly name for the server
   - **Hostname:** Server hostname or IP address
   - **Port:** SSH port (default: 22)
   - **Credentials:** Initial SSH credentials (username/password or SSH key)
3. Click **Add Server**
4. OpsPilot will automatically:
   - Detect the operating system
   - Install and configure Salt minion
   - Register the minion with the OpsPilot backend
   - Start collecting data

### Viewing Server Details

Click on any server in the server list to view its details. You'll see the following tabs:

- **Overview:** Quick stats, recent alerts, server information
- **Metrics:** Real-time CPU, memory, disk, and network metrics
- **Salt Info:** Detailed system information (grains)
- **Services:** Manage system services
- **Processes:** View and manage running processes
- **Packages:** View and update packages
- **Logs:** View system logs
- **Alerts:** View and acknowledge alerts

---

## Real-Time Metrics

### CPU Metrics

**Location:** Server Details → Metrics tab

**Features:**
- **Overall CPU Usage:** Dashboard gauge showing total CPU usage
- **Per-Core CPU:** Individual gauges for each CPU core
- **CPU Breakdown:**
  - **User Time:** CPU time spent in user-space processes
  - **System Time:** CPU time spent in kernel processes
  - **I/O Wait:** CPU time waiting for I/O operations
  - **Idle:** CPU time when idle

**Color Coding:**
- 🟢 **Green:** < 50% usage (healthy)
- 🟡 **Yellow:** 50-70% usage (moderate load)
- 🟠 **Orange:** 70-85% usage (high load)
- 🔴 **Red:** > 85% usage (critical)

**Auto-Refresh:** Real-time updates via SSE (Server-Sent Events)

### Memory Metrics

**Location:** Server Details → Metrics tab

**Features:**
- **Total Memory:** Total installed RAM
- **Used/Total Ratio:** Memory usage with progress bar
- **Swap Usage:** Swap space usage and availability

**Color Coding:**
- 🟢 **Green:** < 50% used
- 🟡 **Yellow:** 50-70% used
- 🟠 **Orange:** 70-85% used
- 🔴 **Red:** > 85% used

### Disk Metrics

**Location:** Server Details → Metrics tab

**Features:**
- **Per-Mountpoint Usage:** Progress bars for each filesystem mount
- **Disk Type:** Filesystem type (ext4, xfs, etc.)
- **Disk Device:** Physical disk device name
- **Available Space:** Free space in GB
- **Used Space:** Used space in GB

**Color Coding:**
- 🟢 **Green:** < 70% used
- 🟡 **Yellow:** 70-85% used
- 🟠 **Orange:** 85-90% used
- 🔴 **Red:** > 90% used

### Load Average

**Location:** Server Details → Metrics tab

**Features:**
- **1-Minute Load:** Average load over last 1 minute
- **5-Minute Load:** Average load over last 5 minutes
- **15-Minute Load:** Average load over last 15 minutes

**Color Coding:**
- 🟢 **Green:** < Number of CPU cores
- 🟡 **Yellow:** 1-2x CPU cores
- 🟠 **Orange:** 2-3x CPU cores
- 🔴 **Red:** > 3x CPU cores

**Time Range Selector:**
- **1 Hour:** Show last 1 hour of data
- **6 Hours:** Show last 6 hours of data
- **24 Hours:** Show last 24 hours of data
- **7 Days:** Show last 7 days of data
- **30 Days:** Show last 30 days of data

---

## Service Management

### Viewing Services

**Location:** Server Details → Services tab

**Features:**
- **Service List:** All system services with their current status
- **Status Badges:** Color-coded status indicators
- **Previous Status:** Shows previous status if changed
- **Last Checked:** Timestamp of last status check
- **Search:** Filter services by name

**Service Status:**
- 🟢 **Running:** Service is running
- 🔴 **Stopped:** Service is stopped
- ⚪ **Unknown:** Service status unknown

### Managing Services

**Actions:**
1. **Start Service:**
   - Click **Start** button on a stopped service
   - OpsPilot will execute `systemctl start <service>`
   - Status will update to "Running" (typically within seconds)

2. **Stop Service:**
   - Click **Stop** button on a running service
   - Confirm the action in the dialog
   - OpsPilot will execute `systemctl stop <service>`
   - Status will update to "Stopped"

3. **Restart Service:**
   - Click **Restart** button on a running service
   - Confirm the action in the dialog
   - OpsPilot will execute `systemctl restart <service>`
   - Service will stop and start again

4. **View Details:**
   - Click **Details** button
   - View detailed information about the service

**Best Practices:**
- Use **Restart** instead of separate Stop/Start for most operations
- Monitor service status after actions to ensure they succeeded
- Check logs if a service fails to start or restart

---

## Process Monitoring

### Viewing Processes

**Location:** Server Details → Processes tab

**Features:**
- **Process List:** All running processes on the server
- **Process Details:** PID, name, command, user, CPU %, Memory %
- **CPU/Memory Bars:** Visual indicators of resource usage
- **Process State:** R (Running), S (Sleeping), D (Uninterruptible), Z (Zombie), T (Stopped), W (Paging)

### Filtering and Sorting

**Filters:**
- **Search:** Search by PID, name, command, or username
- **State:** Filter by process state (e.g., only show Zombie processes)
- **Sort By:** Sort by CPU %, Memory %, PID, Name, User, or Start Time
- **Order:** Ascending or descending

### Managing Processes

**Actions:**
1. **View Details:**
   - Click **Details** button
   - View detailed process information

2. **Kill Process:**
   - Click **Kill** button
   - Confirm the action in the dialog
   - OpsPilot will execute `kill <pid>`
   - Process will be terminated gracefully

3. **Force Kill Process:**
   - Click **Force Kill** button
   - Confirm the action in the dialog
   - OpsPilot will execute `kill -9 <pid>`
   - Process will be terminated immediately (no graceful shutdown)

**Best Practices:**
- Use **Kill** (not Force Kill) whenever possible for graceful shutdown
- Use **Force Kill** only for hung or unresponsive processes
- Check the process command before killing to ensure it's the right process
- Monitor system logs after killing critical processes

---

## Package Management

### Viewing Packages

**Location:** Server Details → Packages tab

**Features:**
- **Package List:** All installed packages on the server
- **Version Information:** Current version and available update version
- **Update Indicators:** Shows which packages have updates available
- **Security Updates:** Highlights packages with security-related updates
- **Package Source:** Package manager source (apt, yum, dnf, pip, npm, etc.)
- **Architecture:** Package architecture (amd64, arm64, etc.)

### Filtering Packages

**Filters:**
- **Search:** Search by package name or version
- **Source:** Filter by package manager source
- **Architecture:** Filter by architecture
- **Show Only Updates:** Display only packages with updates available

### Managing Packages

**Actions:**
1. **Update Package:**
   - Click **Update** button on a package with available update
   - Confirm the action in the dialog
   - OpsPilot will execute package manager update command
   - Package will be updated to the latest version

2. **Remove Package:**
   - Click **Remove** button on any package
   - Confirm the action in the dialog (cannot be undone)
   - OpsPilot will execute package manager remove command
   - Package will be removed from the system

3. **Update All Packages:**
   - Click **Update All** button in the bulk actions section
   - Confirm the action in the dialog
   - OpsPilot will update all packages with available updates
   - This may take several minutes for large updates

**Best Practices:**
- Review security updates first and apply them immediately
- Test updates on non-production servers first
- Check logs after package updates for any issues
- Monitor system stability after bulk updates

---

## Log Aggregation

### Viewing Logs

**Location:** Server Details → Logs tab

**Features:**
- **Real-Time Logs:** Live log streaming from the server
- **Log Levels:** DEBUG, INFO, WARN, ERROR
- **Log Sources:** Service or application name
- **Auto-Scroll:** Automatically scroll to latest log entries
- **Search:** Search log messages, sources, or metadata
- **Filter by Level:** Show only logs of specific level
- **Filter by Source:** Show only logs from specific source

### Filtering Logs

**Filters:**
- **Search:** Search by log message, source, or metadata
- **Level:** Filter by log level (DEBUG, INFO, WARN, ERROR)
- **Source:** Filter by log source (e.g., nginx, postgresql)

### Managing Logs

**Actions:**
1. **Auto-Scroll Toggle:**
   - Click **Pause** to stop auto-scrolling
   - Click **Auto Scroll** to resume
   - Useful when reviewing historical logs

2. **Download Logs:**
   - Click **Download** button
   - Logs will be downloaded as JSON file
   - Includes all log entries with metadata

3. **Clear Logs:**
   - Click **Clear** button
   - Confirm the action in the dialog
   - All logs will be removed from the UI (logs are still stored in the database)

**Best Practices:**
- Use **Pause** when investigating specific log entries
- Download logs for offline analysis or record-keeping
- Clear logs periodically to improve UI performance
- Check ERROR logs first when troubleshooting issues

---

## Alert System

### Viewing Alerts

**Location:** Server Details → Alerts tab

**Features:**
- **Alert List:** All system alerts
- **Severity Levels:** Info, Warning, Critical
- **Alert Types:** CPU high, memory high, disk full, service down, etc.
- **Unread Indicator:** Badge showing number of unread alerts
- **Search:** Search by alert type, message, or event data
- **Filter by Severity:** Show only alerts of specific severity
- **Filter by Type:** Show only alerts of specific type

### Alert Severity

- 🔵 **Info:** Informational alerts (e.g., system update available)
- 🟡 **Warning:** Warning alerts (e.g., disk usage > 70%)
- 🔴 **Critical:** Critical alerts (e.g., CPU usage > 90%, service down)

### Managing Alerts

**Actions:**
1. **Acknowledge Alert:**
   - Click **Acknowledge** button on an alert
   - Alert will be marked as acknowledged (read)
   - Unread badge count will decrease

2. **Acknowledge All:**
   - Click **Acknowledge All** button in the header
   - All unread alerts will be acknowledged
   - Unread badge will be cleared

3. **View Details:**
   - Click **Details** button
   - View detailed alert information including event data

4. **Clear All Alerts:**
   - Click **Clear All** button
   - Confirm the action in the dialog
   - All alerts will be removed from the UI

**Browser Notifications:**
- Critical alerts will trigger browser notifications (if enabled)
- Click notification to navigate to the Alerts tab

**Best Practices:**
- Acknowledge alerts after investigating and resolving issues
- Review Critical alerts first as they indicate urgent problems
- Check logs and metrics when investigating alerts
- Document alert resolution for future reference

---

## Salt Minion Information

### Viewing Minion Information

**Location:** Server Details → Salt Info tab

**Features:**
- **Minion Status:** Online, Warning, or Offline
- **Last Seen:** Timestamp of last communication
- **Uptime:** How long the minion has been running
- **Last Highstate:** When the last Salt highstate was run

### System Information

**Location:** Server Details → Salt Info tab → System Information

**Details:**
- **OS Family:** Operating system family (Debian, RHEL, etc.)
- **OS Name:** Full operating system name
- **OS Release:** Operating system version
- **Kernel:** Linux kernel version
- **Architecture:** System architecture (amd64, arm64, etc.)
- **Hostname:** Server hostname
- **FQDN:** Fully qualified domain name
- **Domain:** DNS domain
- **Virtual:** Whether running in a virtual machine
- **Timezone:** System timezone

### Hardware Information

**Location:** Server Details → Salt Info tab → Hardware Information

**Details:**
- **CPU Model:** CPU model name
- **CPU Cores:** Number of CPU cores
- **CPU Architecture:** CPU architecture
- **Total Memory:** Total installed RAM
- **Manufacturer:** Hardware manufacturer
- **Product Name:** Product name
- **Serial Number:** Hardware serial number
- **BIOS Vendor:** BIOS vendor
- **BIOS Version:** BIOS version
- **BIOS Release:** BIOS release date

### Storage Information

**Location:** Server Details → Salt Info tab → Storage Information

**Disks:**
- **Disk Name:** Disk device name (e.g., /dev/sda)
- **Disk Type:** SSD or HDD
- **Disk Size:** Total disk size
- **Disk Model:** Disk model name

**Filesystems:**
- **Mount Point:** Mount point (e.g., /, /var, /home)
- **Filesystem Type:** ext4, xfs, etc.
- **Usage:** Used percentage
- **Total:** Total space
- **Used:** Used space
- **Available:** Available space

### Network Information

**Location:** Server Details → Salt Info tab → Network Information

**Network Interfaces:**
- **Interface Name:** Network interface (e.g., eth0, wlan0)
- **MAC Address:** Hardware MAC address
- **IPv4 Address:** IPv4 IP address
- **IPv4 Netmask:** IPv4 subnet mask
- **IPv4 Gateway:** Default gateway
- **IPv6 Address:** IPv6 IP address (if configured)
- **IPv6 Prefix:** IPv6 prefix
- **IPv6 Scope:** IPv6 scope (global, link-local, etc.)
- **MTU:** Maximum transmission unit

**System DNS:**
- **Nameservers:** DNS servers (e.g., 8.8.8.8, 1.1.1.1)
- **Search Domains:** DNS search domains

### Refreshing Grains

**Action:**
- Click **Refresh Grains** button
- OpsPilot will request updated grain information from the minion
- All information will be updated

---

## Troubleshooting

### Common Issues

**Minion Offline:**
- Check network connectivity between minion and backend
- Verify Salt minion is running: `systemctl status salt-minion`
- Check Salt minion logs: `journalctl -u salt-minion`

**No Metrics Displaying:**
- Verify SSE connection status (check browser console)
- Check Redis is running on the backend
- Verify JWT token is valid (re-login if needed)

**Service Start Fails:**
- Check service logs in the Logs tab
- Verify service configuration is correct
- Check system logs for errors

**Process Won't Kill:**
- Try **Force Kill** instead of regular **Kill**
- Check if process is a kernel process (may not be killable)
- Verify you have sufficient permissions

### Getting Help

- **Documentation:** Check the [Deployment Guide](deployment-guide.md) for configuration help
- **Logs:** Review system logs in the Logs tab
- **Status:** Check SSE connection status in Metrics tab
- **Support:** Contact OpsPilot support team for assistance

---

## Permissions

### User Roles

- **Admin:** Full access to all features
- **DevOps:** Read/write access to all features
- **Viewer:** Read-only access (no service/package management)

### Access Control

- Users can only access servers in their organization
- Server-specific SSE connections require appropriate permissions
- Admin users can view all servers in their organization

---

## Best Practices

### Performance Monitoring

- Monitor CPU, memory, and disk usage regularly
- Set up alert thresholds appropriate for your workload
- Review historical metrics to identify trends
- Investigate sustained high resource usage

### Service Management

- Start/stop/restart services during maintenance windows
- Monitor service logs after changes
- Keep service documentation up-to-date
- Test service changes in non-production environments first

### Security

- Apply security updates immediately
- Review critical alerts as soon as possible
- Monitor for unusual process activity
- Keep system packages up-to-date

### Backup

- Regularly back up important data
- Test backup restoration procedures
- Monitor disk space to ensure backup completion
- Document backup and restore procedures

---

## Glossary

- **Salt Minion:** Salt agent running on managed servers
- **Grains:** Static system information collected by Salt
- **Highstate:** Salt's desired state configuration
- **Beacon:** Salt's event-based monitoring system
- **SSE:** Server-Sent Events for real-time data streaming
- **PID:** Process ID
- **CPU:** Central Processing Unit
- **RAM:** Random Access Memory
- **SSD:** Solid State Drive
- **HDD:** Hard Disk Drive
- **MTU:** Maximum Transmission Unit
- **FQDN:** Fully Qualified Domain Name

---

## Next Steps

- **Deployment:** See [Deployment Guide](deployment-guide.md)
- **API Documentation:** See [Swagger UI](http://localhost:8000/docs)
- **Testing:** See [Testing Guide](testing-guide.md)

---

**Last Updated:** 2026-04-17
**Version:** 1.0.0

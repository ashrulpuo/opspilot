# Monitoring State
# Installs and configures Prometheus node_exporter

node-exporter:
  pkg.installed:
    - name: prometheus-node-exporter
    - version: latest

node-exporter-service:
  service.running:
    - name: prometheus-node-exporter
    - enable: True

node-exporter-firewall:
  firewalld.present:
    - name: public
    - ports:
      - 9100/tcp
    - onlyif:
      - rpm -q firewalld

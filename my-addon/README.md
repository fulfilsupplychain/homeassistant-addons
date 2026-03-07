# System Monitor

Real-time system monitoring with **REST** and **MQTT** transport. Publishes CPU, RAM, disk, temperature, network, and **service health** as native Home Assistant sensor entities.

![Version](https://img.shields.io/badge/version-3.0.0-blue)

## Features

### Transport Modes

| Mode               | Use Case                   | How it Works                                    |
| ------------------ | -------------------------- | ----------------------------------------------- |
| **REST** (default) | Monitoring the HA host     | Posts via Supervisor API                        |
| **MQTT**           | Monitoring remote machines | Publishes to MQTT broker with HA auto-discovery |

### Sensors Published

| Entity                                | Description                 | Unit  |
| ------------------------------------- | --------------------------- | ----- |
| `sensor.system_monitor_cpu_usage`     | CPU utilization             | %     |
| `sensor.system_monitor_cpu_frequency` | CPU frequency               | MHz   |
| `sensor.system_monitor_cpu_cores`     | Per-core usage (attributes) | %     |
| `sensor.system_monitor_load_1m`       | Load average 1 min          | —     |
| `sensor.system_monitor_ram_usage`     | RAM utilization             | %     |
| `sensor.system_monitor_ram_used`      | RAM used                    | GB    |
| `sensor.system_monitor_swap_usage`    | Swap utilization            | %     |
| `sensor.system_monitor_disk_*`        | Disk usage per partition    | %     |
| `sensor.system_monitor_disk_primary`  | Largest partition           | %     |
| `sensor.system_monitor_temp_*`        | Temperature sensors         | °C    |
| `sensor.system_monitor_net_sent`      | Network sent                | MB    |
| `sensor.system_monitor_net_received`  | Network received            | MB    |
| `sensor.system_monitor_uptime`        | System uptime               | hours |
| `sensor.system_monitor_host_info`     | Hostname & platform         | —     |
| `sensor.system_monitor_top_processes` | Top 5 by CPU                | —     |

### Binary Sensors (Service Health)

| Entity                                        | What it checks   |
| --------------------------------------------- | ---------------- |
| `binary_sensor.system_monitor_service_docker` | Docker daemon    |
| `binary_sensor.system_monitor_service_nginx`  | Nginx web server |
| `binary_sensor.system_monitor_service_sshd`   | SSH server       |
| _...any custom service_                       | Configurable     |

## Installation

1. **Settings → Add-ons → Add-on Store** → ⋮ → **Repositories**
2. Add: `https://github.com/fulfilsupplychain/homeassistant-addons`
3. Install **System Monitor** → Start

## Configuration

```yaml
refresh_interval: 5 # Update frequency (1-60 seconds)
transport_mode: rest # "rest" or "mqtt"

# MQTT settings (only if transport_mode: mqtt)
mqtt_host: core-mosquitto # Broker hostname
mqtt_port: 1883
mqtt_user: ""
mqtt_pass: ""
mqtt_topic_prefix: system_monitor

# Service health monitoring
watched_services:
  - docker
  - nginx
  - sshd
  - mosquitto

log_level: info
```

### MQTT Mode

When using MQTT mode:

1. Ensure the **Mosquitto broker** add-on (or external broker) is running
2. Set `transport_mode: mqtt` and configure broker credentials
3. Sensors will auto-register in HA via **MQTT Discovery**
4. Works from **any machine** — not just the HA host

## Dashboard

Import the included `dashboard.yaml` into HA:

1. **Settings → Dashboards → + ADD DASHBOARD**
2. Open → ✏️ Edit → ⋮ → **Raw configuration editor**
3. Paste contents of `dashboard.yaml` → **Save**

## Support

[GitHub Issues](https://github.com/fulfilsupplychain/homeassistant-addons/issues)

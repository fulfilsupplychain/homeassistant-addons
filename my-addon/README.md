# System Monitor

Publishes real-time system metrics as **native Home Assistant sensor entities**, so you can use them on any HA dashboard with built-in cards.

![Version](https://img.shields.io/badge/version-2.0.0-blue) ![HA Dashboard](https://img.shields.io/badge/HA-native%20dashboard-blue)

## About

This add-on monitors your Home Assistant host and publishes system metrics as regular HA sensor entities (e.g., `sensor.system_monitor_cpu_usage`). You can display them using **any** native HA dashboard card — gauges, history graphs, entity cards, and more.

### Sensors Published

| Entity                                | Description                    | Unit  |
| ------------------------------------- | ------------------------------ | ----- |
| `sensor.system_monitor_cpu_usage`     | Total CPU utilization          | %     |
| `sensor.system_monitor_cpu_frequency` | Current CPU frequency          | MHz   |
| `sensor.system_monitor_cpu_cores`     | Per-core usage (in attributes) | %     |
| `sensor.system_monitor_load_1m`       | Load average (1 min)           | —     |
| `sensor.system_monitor_ram_usage`     | RAM utilization                | %     |
| `sensor.system_monitor_ram_used`      | RAM used                       | GB    |
| `sensor.system_monitor_swap_usage`    | Swap utilization               | %     |
| `sensor.system_monitor_disk_root`     | Root disk usage                | %     |
| `sensor.system_monitor_temp_*`        | Temperature sensors            | °C    |
| `sensor.system_monitor_net_sent`      | Network bytes sent             | MB    |
| `sensor.system_monitor_net_received`  | Network bytes received         | MB    |
| `sensor.system_monitor_uptime`        | System uptime                  | hours |
| `sensor.system_monitor_host_info`     | Hostname & platform info       | —     |
| `sensor.system_monitor_top_processes` | Top 5 processes by CPU         | —     |

## Installation

1. Navigate to **Settings → Add-ons → Add-on Store** in HA.
2. Click **⋮** → **Repositories**.
3. Add this URL:
   ```
   https://github.com/fulfilsupplychain/homeassistant-addons
   ```
4. Find **System Monitor** and click **Install**.
5. **Start** the add-on.

## Dashboard Setup

A ready-to-import dashboard config is included in [`dashboard.yaml`](./dashboard.yaml).

### Quick Import

1. Go to **Settings → Dashboards → + Add Dashboard**
2. Name it "System Monitor", pick icon `mdi:chart-box`
3. Open the dashboard → **⋮** → **Edit dashboard**
4. Click **⋮** → **Raw configuration editor**
5. Paste the contents of `dashboard.yaml`
6. Click **Save**

This gives you:

- **Gauge cards** for CPU, RAM, Swap, and Disk
- **Entity cards** with detailed info
- **History graphs** for trending over time

## Configuration

| Option             | Description                                    | Default |
| ------------------ | ---------------------------------------------- | ------- |
| `refresh_interval` | How often to update sensors, in seconds (1–60) | `5`     |
| `log_level`        | Logging verbosity                              | `info`  |

```yaml
refresh_interval: 5
log_level: info
```

## Support

- Open an issue on the [GitHub repository](https://github.com/fulfilsupplychain/homeassistant-addons/issues).

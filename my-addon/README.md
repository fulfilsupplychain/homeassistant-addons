# System Monitor Dashboard

A real-time system monitoring dashboard for Home Assistant, showing CPU, RAM, disk, temperatures, network, and processes.

![Dashboard](https://img.shields.io/badge/dashboard-live-brightgreen) ![Version](https://img.shields.io/badge/version-1.1.0-blue)

## About

This add-on provides a beautiful, real-time web dashboard that monitors your Home Assistant host system. It is accessible directly from the HA sidebar via ingress.

### Features

- 🔵 **CPU Usage** — Total and per-core utilization with frequency and load averages
- 💚 **RAM Usage** — Used, total, and available memory with percentage gauge
- 🟠 **Swap Usage** — Swap utilization monitoring
- 🟣 **Disk Usage** — All mounted partitions with capacity breakdown
- 🌡️ **Temperatures** — Sensor readings with color-coded warnings (high/critical)
- 🌐 **Network I/O** — Bytes and packets sent/received
- 📊 **Top Processes** — Top 10 processes by CPU usage
- 🔄 **Auto-refresh** — Configurable polling interval (default: 2 seconds)
- 🌙 **Dark Mode** — Premium glassmorphism design with smooth animations

## Installation

1. Navigate to **Settings → Add-ons → Add-on Store** in your Home Assistant instance.
2. Click the **⋮** menu (top right) → **Repositories**.
3. Add this repository URL:
   ```
   https://github.com/fulfilsupplychain/homeassistant-addons
   ```
4. Find **System Monitor Dashboard** in the store and click **Install**.
5. Start the add-on — it will appear in your HA sidebar.

## Configuration

| Option             | Description                                  | Default |
| ------------------ | -------------------------------------------- | ------- |
| `refresh_interval` | Dashboard polling interval in seconds (1–60) | `2`     |
| `log_level`        | Logging verbosity                            | `info`  |

### Example configuration

```yaml
refresh_interval: 2
log_level: info
```

## Architecture

```
my-addon/
├── config.yaml                     # Add-on configuration
├── build.yaml                      # Architecture → base image map
├── Dockerfile                      # Container build
├── run.sh                          # Entrypoint (starts Python server)
└── rootfs/opt/system-monitor/
    ├── server.py                   # Python HTTP server + API
    └── www/
        └── index.html              # Dashboard (HTML + CSS + JS)
```

**Tech Stack:**

- **Backend:** Python 3 + `psutil` + built-in `http.server`
- **Frontend:** Vanilla HTML/CSS/JS (no framework dependencies)
- **API:** JSON endpoint at `/api/stats` polled by the dashboard

## Support

- Open an issue on the [GitHub repository](https://github.com/fulfilsupplychain/homeassistant-addons/issues).

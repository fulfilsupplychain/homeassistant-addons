# Changelog

## 3.0.0

### MQTT Transport

- 🔌 **Dual transport**: REST (Supervisor API) and MQTT modes
- 📡 **MQTT Auto-Discovery**: sensors auto-register in HA
- 🌐 **Remote monitoring**: monitor any machine over MQTT, not just the HA host
- 💓 **Availability tracking**: online/offline status via MQTT will messages
- 🔐 **MQTT authentication**: username/password support

### Binary Sensors (Service Health)

- 🩺 **Service monitoring**: watch critical processes (Docker, Nginx, SSH, etc.)
- ✅ `binary_sensor.system_monitor_service_<name>` — ON when running, OFF when stopped
- 🔧 Checks via systemd first, falls back to process name matching
- 📋 User-configurable service list

### Improvements

- 🏗️ Unified publisher abstraction (REST/MQTT)
- 📊 Updated dashboard with Service Health card
- 🔄 Host info now publishes every cycle (not just at startup)

## 2.0.0

- 🏠 Native HA Dashboard integration — metrics as HA sensor entities
- 📊 Ready-to-import dashboard.yaml
- ❌ Removed standalone web dashboard

## 1.1.0

- 🖥️ Standalone web dashboard with real-time stats

## 1.0.0

- 🎉 Initial release

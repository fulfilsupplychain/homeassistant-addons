#!/usr/bin/with-contenv bashio
# ==============================================================================
# Home Assistant Add-on: System Monitor
# Publishes system metrics as native HA sensor entities
# ==============================================================================

# --- Read user configuration ---
declare REFRESH_INTERVAL
declare LOG_LEVEL

REFRESH_INTERVAL=$(bashio::config 'refresh_interval')
LOG_LEVEL=$(bashio::config 'log_level')

bashio::log.level "${LOG_LEVEL}"

# --- Export env variables for the Python publisher ---
export REFRESH_INTERVAL
export SUPERVISOR_TOKEN="${SUPERVISOR_TOKEN}"

bashio::log.info "========================================"
bashio::log.info " System Monitor v2.0.0"
bashio::log.info "========================================"
bashio::log.info "Refresh interval: ${REFRESH_INTERVAL}s"
bashio::log.info "Log level: ${LOG_LEVEL}"
bashio::log.info "========================================"
bashio::log.info ""
bashio::log.info "Sensors will appear as sensor.system_monitor_*"
bashio::log.info "Use them on any Home Assistant dashboard!"
bashio::log.info ""

# --- Start the sensor publisher ---
bashio::log.info "Starting system monitor sensor publisher..."
exec python3 /opt/system-monitor/server.py

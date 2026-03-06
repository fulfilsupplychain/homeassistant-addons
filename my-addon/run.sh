#!/usr/bin/with-contenv bashio
# ==============================================================================
# Home Assistant Add-on: System Monitor Dashboard
# Starts the Python web server that serves the monitoring dashboard
# ==============================================================================

# --- Read user configuration ---
declare REFRESH_INTERVAL
declare LOG_LEVEL

REFRESH_INTERVAL=$(bashio::config 'refresh_interval')
LOG_LEVEL=$(bashio::config 'log_level')

bashio::log.level "${LOG_LEVEL}"

# --- Export env variables for the Python server ---
export INGRESS_PORT=$(bashio::addon.ingress_port)
export INGRESS_ENTRY=$(bashio::addon.ingress_entry)

bashio::log.info "========================================"
bashio::log.info " System Monitor Dashboard"
bashio::log.info "========================================"
bashio::log.info "Ingress port: ${INGRESS_PORT}"
bashio::log.info "Ingress entry: ${INGRESS_ENTRY}"
bashio::log.info "Refresh interval: ${REFRESH_INTERVAL}s"
bashio::log.info "Log level: ${LOG_LEVEL}"
bashio::log.info "========================================"

# --- Start the web server ---
bashio::log.info "Starting System Monitor web server..."
exec python3 /opt/system-monitor/server.py

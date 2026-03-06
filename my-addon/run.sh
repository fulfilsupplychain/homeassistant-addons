#!/usr/bin/with-contenv bashio
# ==============================================================================
# Home Assistant Add-on: My Addon
# Entrypoint script
# ==============================================================================

# --- Read user configuration ---
declare MESSAGE
declare LOG_LEVEL

MESSAGE=$(bashio::config 'message')
LOG_LEVEL=$(bashio::config 'log_level')

bashio::log.level "${LOG_LEVEL}"

# --- Main ---
bashio::log.info "Starting My Addon..."
bashio::log.info "Configuration message: ${MESSAGE}"

# Keep the add-on running
# Replace the loop below with your actual add-on logic
while true; do
    bashio::log.debug "My Addon is running — $(date)"
    sleep 60
done

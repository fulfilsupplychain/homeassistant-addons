#!/usr/bin/with-contenv bashio
# ==============================================================================
# Home Assistant Add-on: System Monitor v3.0.0
# Supports REST and MQTT transport with service health monitoring
# ==============================================================================

# --- Read user configuration ---
REFRESH_INTERVAL=$(bashio::config 'refresh_interval')
TRANSPORT_MODE=$(bashio::config 'transport_mode')
MQTT_HOST=$(bashio::config 'mqtt_host')
MQTT_PORT=$(bashio::config 'mqtt_port')
MQTT_USER=$(bashio::config 'mqtt_user')
MQTT_PASS=$(bashio::config 'mqtt_pass')
MQTT_TOPIC_PREFIX=$(bashio::config 'mqtt_topic_prefix')
LOG_LEVEL=$(bashio::config 'log_level')

# Read watched services as comma-separated string
WATCHED_SERVICES=""
for svc in $(bashio::config 'watched_services'); do
    if [ -n "${WATCHED_SERVICES}" ]; then
        WATCHED_SERVICES="${WATCHED_SERVICES},${svc}"
    else
        WATCHED_SERVICES="${svc}"
    fi
done

bashio::log.level "${LOG_LEVEL}"

# --- Export env variables for the Python publisher ---
export REFRESH_INTERVAL
export TRANSPORT_MODE
export SUPERVISOR_TOKEN="${SUPERVISOR_TOKEN}"
export MQTT_HOST
export MQTT_PORT
export MQTT_USER
export MQTT_PASS
export MQTT_TOPIC_PREFIX
export WATCHED_SERVICES

bashio::log.info "========================================"
bashio::log.info " System Monitor v3.0.0"
bashio::log.info "========================================"
bashio::log.info "Transport:        ${TRANSPORT_MODE}"
bashio::log.info "Refresh interval: ${REFRESH_INTERVAL}s"
if [ "${TRANSPORT_MODE}" = "mqtt" ]; then
    bashio::log.info "MQTT broker:      ${MQTT_HOST}:${MQTT_PORT}"
    bashio::log.info "MQTT topic:       ${MQTT_TOPIC_PREFIX}"
fi
if [ -n "${WATCHED_SERVICES}" ]; then
    bashio::log.info "Watched services: ${WATCHED_SERVICES}"
fi
bashio::log.info "========================================"

# --- Start the sensor publisher ---
exec python3 /opt/system-monitor/server.py

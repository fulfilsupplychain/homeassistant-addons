#!/usr/bin/env python3
"""
System Monitor v3.0.0 — HA Sensor Publisher
Supports REST (Supervisor API) and MQTT transports.
Publishes system metrics + binary sensors for service health.
"""

import json
import re
import os
import time
import socket
import platform
import subprocess
import urllib.request
import urllib.error

import psutil


# ─── Configuration ──────────────────────────────────────────────────────────────

REFRESH_INTERVAL = int(os.environ.get("REFRESH_INTERVAL", 5))
TRANSPORT_MODE = os.environ.get("TRANSPORT_MODE", "rest").lower()  # "rest" or "mqtt"

# REST config
SUPERVISOR_TOKEN = os.environ.get("SUPERVISOR_TOKEN", "")
HA_API_URL = "http://supervisor/core/api"
REST_HEADERS = {
    "Authorization": f"Bearer {SUPERVISOR_TOKEN}",
    "Content-Type": "application/json",
}

# MQTT config
MQTT_HOST = os.environ.get("MQTT_HOST", "core-mosquitto")
MQTT_PORT = int(os.environ.get("MQTT_PORT", 1883))
MQTT_USER = os.environ.get("MQTT_USER", "")
MQTT_PASS = os.environ.get("MQTT_PASS", "")
MQTT_TOPIC_PREFIX = os.environ.get("MQTT_TOPIC_PREFIX", "system_monitor")
MQTT_DISCOVERY_PREFIX = os.environ.get("MQTT_DISCOVERY_PREFIX", "homeassistant")

# Services to watch (comma-separated)
WATCHED_SERVICES = [
    s.strip() for s in os.environ.get("WATCHED_SERVICES", "").split(",") if s.strip()
]

ENTITY_PREFIX = "sensor.system_monitor"
DEVICE_ID = os.environ.get("DEVICE_ID", socket.gethostname())

# Global MQTT client
mqtt_client = None


# ─── Helpers ────────────────────────────────────────────────────────────────────

def sanitize_entity_slug(text):
    """Convert text to a valid HA entity ID fragment (lowercase, a-z 0-9 _ only)."""
    slug = text.lower().strip("/")
    slug = re.sub(r'[^a-z0-9]+', '_', slug)
    slug = slug.strip('_')
    return slug or "unknown"


# ─── MQTT Transport ─────────────────────────────────────────────────────────────

def mqtt_connect():
    """Connect to the MQTT broker."""
    global mqtt_client
    try:
        import paho.mqtt.client as mqtt_lib
    except ImportError:
        print("[system-monitor] ERROR: paho-mqtt not installed. Use 'rest' mode.", flush=True)
        return False

    mqtt_client = mqtt_lib.Client(
        client_id=f"system_monitor_{DEVICE_ID}",
        protocol=mqtt_lib.MQTTv311,
    )

    if MQTT_USER:
        mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)

    # Will message — marks device as offline when disconnected
    mqtt_client.will_set(
        f"{MQTT_TOPIC_PREFIX}/status",
        payload="offline",
        qos=1,
        retain=True,
    )

    try:
        mqtt_client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
        mqtt_client.loop_start()
        # Publish birth message
        mqtt_client.publish(f"{MQTT_TOPIC_PREFIX}/status", "online", qos=1, retain=True)
        print(f"[system-monitor] MQTT connected to {MQTT_HOST}:{MQTT_PORT}", flush=True)
        return True
    except Exception as e:
        print(f"[system-monitor] MQTT connection failed: {e}", flush=True)
        return False


def mqtt_publish_discovery(component, object_id, name, config_extra=None):
    """Publish an MQTT auto-discovery message for a sensor/binary_sensor."""
    if mqtt_client is None:
        return

    unique_id = f"system_monitor_{DEVICE_ID}_{object_id}"
    topic = f"{MQTT_DISCOVERY_PREFIX}/{component}/{unique_id}/config"

    config = {
        "name": name,
        "unique_id": unique_id,
        "state_topic": f"{MQTT_TOPIC_PREFIX}/{object_id}/state",
        "json_attributes_topic": f"{MQTT_TOPIC_PREFIX}/{object_id}/attributes",
        "availability": {
            "topic": f"{MQTT_TOPIC_PREFIX}/status",
            "payload_available": "online",
            "payload_not_available": "offline",
        },
        "device": {
            "identifiers": [f"system_monitor_{DEVICE_ID}"],
            "name": f"System Monitor ({DEVICE_ID})",
            "model": "System Monitor Add-on",
            "manufacturer": "Fulfil Supply Chain",
            "sw_version": "3.0.0",
        },
    }

    if config_extra:
        config.update(config_extra)

    mqtt_client.publish(topic, json.dumps(config), qos=1, retain=True)


def mqtt_publish_state(object_id, state, attributes=None):
    """Publish state and attributes to MQTT."""
    if mqtt_client is None:
        return
    mqtt_client.publish(f"{MQTT_TOPIC_PREFIX}/{object_id}/state", str(state), qos=0)
    if attributes:
        mqtt_client.publish(
            f"{MQTT_TOPIC_PREFIX}/{object_id}/attributes",
            json.dumps(attributes),
            qos=0,
        )


# ─── REST Transport ─────────────────────────────────────────────────────────────

def rest_post_state(entity_id, state, attributes):
    """Push a sensor entity state to HA via the Supervisor proxy."""
    url = f"{HA_API_URL}/states/{entity_id}"
    payload = json.dumps({"state": state, "attributes": attributes}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers=REST_HEADERS, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        print(f"[system-monitor] HTTP {e.code} posting {entity_id}: {e.reason}", flush=True)
    except urllib.error.URLError as e:
        print(f"[system-monitor] URL error posting {entity_id}: {e.reason}", flush=True)
    except Exception as e:
        print(f"[system-monitor] Error posting {entity_id}: {e}", flush=True)
    return None


# ─── Unified Publisher ──────────────────────────────────────────────────────────

def publish_sensor(object_id, state, attributes, friendly_name=None):
    """Publish a sensor value via the configured transport."""
    if TRANSPORT_MODE == "mqtt":
        mqtt_publish_state(object_id, state, attributes)
    else:
        entity_id = f"{ENTITY_PREFIX}_{object_id}"
        attrs = dict(attributes)
        if friendly_name:
            attrs["friendly_name"] = friendly_name
        rest_post_state(entity_id, str(state), attrs)


def publish_binary_sensor(object_id, is_on, attributes, friendly_name=None):
    """Publish a binary sensor value via the configured transport."""
    state_str = "ON" if is_on else "OFF"
    if TRANSPORT_MODE == "mqtt":
        mqtt_publish_state(object_id, state_str, attributes)
    else:
        entity_id = f"binary_sensor.system_monitor_{object_id}"
        attrs = dict(attributes)
        if friendly_name:
            attrs["friendly_name"] = friendly_name
        rest_post_state(entity_id, "on" if is_on else "off", attrs)


# ─── MQTT Discovery Registration ────────────────────────────────────────────────

def register_mqtt_discovery():
    """Send MQTT Discovery configs for all sensors and binary_sensors."""
    # Sensors
    sensors = [
        ("cpu_usage", "CPU Usage", {"unit_of_measurement": "%", "icon": "mdi:cpu-64-bit", "state_class": "measurement"}),
        ("cpu_frequency", "CPU Frequency", {"unit_of_measurement": "MHz", "icon": "mdi:sine-wave", "state_class": "measurement"}),
        ("cpu_cores", "CPU Cores", {"unit_of_measurement": "%", "icon": "mdi:chip", "state_class": "measurement"}),
        ("load_1m", "Load Average 1m", {"icon": "mdi:gauge", "state_class": "measurement"}),
        ("ram_usage", "RAM Usage", {"unit_of_measurement": "%", "icon": "mdi:memory", "state_class": "measurement"}),
        ("ram_used", "RAM Used", {"unit_of_measurement": "GB", "icon": "mdi:memory", "device_class": "data_size", "state_class": "measurement"}),
        ("swap_usage", "Swap Usage", {"unit_of_measurement": "%", "icon": "mdi:swap-horizontal", "state_class": "measurement"}),
        ("disk_primary", "Disk Primary", {"unit_of_measurement": "%", "icon": "mdi:harddisk", "state_class": "measurement"}),
        ("net_sent", "Network Sent", {"unit_of_measurement": "MB", "icon": "mdi:upload-network", "device_class": "data_size", "state_class": "total_increasing"}),
        ("net_received", "Network Received", {"unit_of_measurement": "MB", "icon": "mdi:download-network", "device_class": "data_size", "state_class": "total_increasing"}),
        ("uptime", "Uptime", {"unit_of_measurement": "h", "icon": "mdi:clock-check-outline", "state_class": "total_increasing"}),
        ("host_info", "Host Info", {"icon": "mdi:server"}),
        ("top_processes", "Top Processes", {"icon": "mdi:format-list-numbered"}),
    ]
    for obj_id, name, extra in sensors:
        mqtt_publish_discovery("sensor", obj_id, name, extra)

    # Binary sensors for watched services
    for svc in WATCHED_SERVICES:
        svc_slug = sanitize_entity_slug(svc)
        mqtt_publish_discovery("binary_sensor", f"service_{svc_slug}", f"Service {svc}", {
            "device_class": "running",
            "icon": "mdi:cog",
            "payload_on": "ON",
            "payload_off": "OFF",
        })

    print(f"[system-monitor] MQTT Discovery: registered {len(sensors)} sensors + {len(WATCHED_SERVICES)} services", flush=True)


# ─── Metric Collectors ──────────────────────────────────────────────────────────

def publish_cpu():
    """Publish CPU metrics."""
    cpu_pct = psutil.cpu_percent()
    freq = psutil.cpu_freq()
    per_core = psutil.cpu_percent(percpu=True)
    load = list(psutil.getloadavg()) if hasattr(psutil, "getloadavg") else [0, 0, 0]

    publish_sensor("cpu_usage", round(cpu_pct, 1), {
        "unit_of_measurement": "%",
        "icon": "mdi:cpu-64-bit",
        "state_class": "measurement",
        "cores_logical": psutil.cpu_count(logical=True),
        "cores_physical": psutil.cpu_count(logical=False),
        "frequency_mhz": round(freq.current, 1) if freq else None,
        "frequency_max_mhz": round(freq.max, 1) if freq else None,
        "load_1m": round(load[0], 2),
        "load_5m": round(load[1], 2),
        "load_15m": round(load[2], 2),
    }, "System Monitor CPU Usage")

    if freq:
        publish_sensor("cpu_frequency", round(freq.current, 0), {
            "unit_of_measurement": "MHz",
            "icon": "mdi:sine-wave",
            "state_class": "measurement",
            "max_frequency_mhz": round(freq.max, 1) if freq.max else None,
        }, "System Monitor CPU Frequency")

    core_attrs = {f"core_{i}": round(v, 1) for i, v in enumerate(per_core)}
    core_attrs["unit_of_measurement"] = "%"
    core_attrs["icon"] = "mdi:chip"
    core_attrs["core_count"] = len(per_core)
    publish_sensor("cpu_cores", round(cpu_pct, 1), core_attrs, "System Monitor CPU Cores")

    publish_sensor("load_1m", round(load[0], 2), {
        "icon": "mdi:gauge",
        "state_class": "measurement",
        "load_5m": round(load[1], 2),
        "load_15m": round(load[2], 2),
    }, "System Monitor Load 1m")


def publish_memory():
    """Publish RAM and Swap metrics."""
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    publish_sensor("ram_usage", round(mem.percent, 1), {
        "unit_of_measurement": "%",
        "icon": "mdi:memory",
        "state_class": "measurement",
        "total_gb": round(mem.total / (1024**3), 2),
        "used_gb": round(mem.used / (1024**3), 2),
        "available_gb": round(mem.available / (1024**3), 2),
    }, "System Monitor RAM Usage")

    publish_sensor("ram_used", round(mem.used / (1024**3), 2), {
        "unit_of_measurement": "GB",
        "icon": "mdi:memory",
        "device_class": "data_size",
        "state_class": "measurement",
    }, "System Monitor RAM Used")

    swap_pct = swap.percent if swap.total > 0 else 0
    publish_sensor("swap_usage", round(swap_pct, 1), {
        "unit_of_measurement": "%",
        "icon": "mdi:swap-horizontal",
        "state_class": "measurement",
        "total_gb": round(swap.total / (1024**3), 2) if swap.total > 0 else 0,
        "used_gb": round(swap.used / (1024**3), 2) if swap.total > 0 else 0,
        "free_gb": round(swap.free / (1024**3), 2) if swap.total > 0 else 0,
    }, "System Monitor Swap Usage")


def publish_disks():
    """Publish disk usage metrics."""
    SKIP_MOUNTS = {"/etc/resolv.conf", "/etc/hostname", "/etc/hosts"}
    largest_disk = None
    largest_size = 0

    for part in psutil.disk_partitions(all=False):
        if part.mountpoint in SKIP_MOUNTS:
            continue
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except (PermissionError, OSError):
            continue

        slug = sanitize_entity_slug(part.mountpoint)
        mount_slug = slug if slug else "root"

        attrs = {
            "unit_of_measurement": "%",
            "icon": "mdi:harddisk",
            "state_class": "measurement",
            "device": part.device,
            "mountpoint": part.mountpoint,
            "filesystem": part.fstype,
            "total_gb": round(usage.total / (1024**3), 2),
            "used_gb": round(usage.used / (1024**3), 2),
            "free_gb": round(usage.free / (1024**3), 2),
        }

        publish_sensor(f"disk_{mount_slug}", round(usage.percent, 1), attrs,
                       f"System Monitor Disk ({part.mountpoint})")

        if usage.total > largest_size:
            largest_size = usage.total
            largest_disk = (usage, attrs)

    if largest_disk:
        usage, attrs = largest_disk
        primary_attrs = dict(attrs)
        publish_sensor("disk_primary", round(usage.percent, 1), primary_attrs,
                       "System Monitor Disk (Primary)")


def publish_temperatures():
    """Publish temperature sensor readings."""
    if not hasattr(psutil, "sensors_temperatures"):
        return
    try:
        temps = psutil.sensors_temperatures()
    except Exception:
        return

    for group_name, sensors in temps.items():
        for i, sensor in enumerate(sensors):
            label = sensor.label or f"{group_name}_{i}"
            label_slug = sanitize_entity_slug(label)

            attrs = {
                "unit_of_measurement": "\u00b0C",
                "icon": "mdi:thermometer",
                "device_class": "temperature",
                "state_class": "measurement",
                "sensor_group": group_name,
            }
            if sensor.high:
                attrs["high_threshold"] = round(sensor.high, 1)
            if sensor.critical:
                attrs["critical_threshold"] = round(sensor.critical, 1)

            publish_sensor(f"temp_{label_slug}", round(sensor.current, 1), attrs,
                           f"System Monitor Temp {label}")


def publish_network():
    """Publish network I/O metrics."""
    counters = psutil.net_io_counters()

    publish_sensor("net_sent", round(counters.bytes_sent / (1024**2), 1), {
        "unit_of_measurement": "MB",
        "icon": "mdi:upload-network",
        "device_class": "data_size",
        "state_class": "total_increasing",
        "bytes": counters.bytes_sent,
        "packets": counters.packets_sent,
    }, "System Monitor Network Sent")

    publish_sensor("net_received", round(counters.bytes_recv / (1024**2), 1), {
        "unit_of_measurement": "MB",
        "icon": "mdi:download-network",
        "device_class": "data_size",
        "state_class": "total_increasing",
        "bytes": counters.bytes_recv,
        "packets": counters.packets_recv,
    }, "System Monitor Network Received")


def publish_uptime():
    """Publish system uptime."""
    uptime_secs = round(time.time() - psutil.boot_time())
    days = uptime_secs // 86400
    hours = (uptime_secs % 86400) // 3600
    minutes = (uptime_secs % 3600) // 60

    publish_sensor("uptime", round(uptime_secs / 3600, 1), {
        "unit_of_measurement": "h",
        "icon": "mdi:clock-check-outline",
        "state_class": "total_increasing",
        "days": days,
        "hours": hours,
        "minutes": minutes,
        "uptime_string": f"{days}d {hours}h {minutes}m",
        "boot_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(psutil.boot_time())),
    }, "System Monitor Uptime")


def publish_host_info():
    """Publish static host information."""
    publish_sensor("host_info", socket.gethostname(), {
        "icon": "mdi:server",
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "cpu_count_physical": psutil.cpu_count(logical=False),
        "cpu_count_logical": psutil.cpu_count(logical=True),
        "ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
    }, "System Monitor Host Info")


def publish_top_processes():
    """Publish top processes."""
    procs = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            info = p.info
            procs.append({
                "pid": info["pid"],
                "name": info["name"],
                "cpu_percent": round(info["cpu_percent"] or 0, 1),
                "memory_percent": round(info["memory_percent"] or 0, 1),
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    procs.sort(key=lambda x: x["cpu_percent"], reverse=True)
    top5 = procs[:5]

    attrs = {
        "icon": "mdi:format-list-numbered",
        "total_processes": len(procs),
    }
    for i, p in enumerate(top5):
        attrs[f"process_{i+1}_name"] = p["name"]
        attrs[f"process_{i+1}_pid"] = p["pid"]
        attrs[f"process_{i+1}_cpu"] = p["cpu_percent"]
        attrs[f"process_{i+1}_ram"] = p["memory_percent"]

    publish_sensor("top_processes", len(procs), attrs, "System Monitor Top Processes")


# ─── Binary Sensor: Service Health ──────────────────────────────────────────────

def is_process_running(name):
    """Check if a process with the given name is currently running."""
    name_lower = name.lower()
    for p in psutil.process_iter(["name"]):
        try:
            if p.info["name"] and p.info["name"].lower() == name_lower:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False


def is_systemd_service_active(name):
    """Check if a systemd service is active (Linux only)."""
    try:
        result = subprocess.run(
            ["systemctl", "is-active", name],
            capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip() == "active"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_service(name):
    """Check a service — tries systemd first, then falls back to process name."""
    # Try systemd (e.g. "nginx", "docker", "sshd")
    if is_systemd_service_active(name):
        return True
    # Fallback: check if a process with this name is running
    return is_process_running(name)


def publish_services():
    """Publish binary sensors for each watched service."""
    if not WATCHED_SERVICES:
        return

    for svc in WATCHED_SERVICES:
        svc_slug = sanitize_entity_slug(svc)
        is_running = check_service(svc)

        publish_binary_sensor(f"service_{svc_slug}", is_running, {
            "icon": "mdi:cog-outline" if is_running else "mdi:cog-off",
            "device_class": "running",
            "service_name": svc,
            "checked_at": time.strftime("%H:%M:%S"),
        }, f"System Monitor Service {svc}")


# ─── Main Loop ──────────────────────────────────────────────────────────────────

def main():
    print("[system-monitor] ═══════════════════════════════════════", flush=True)
    print("[system-monitor] System Monitor v3.0.0", flush=True)
    print(f"[system-monitor] Transport: {TRANSPORT_MODE.upper()}", flush=True)
    print(f"[system-monitor] Refresh interval: {REFRESH_INTERVAL}s", flush=True)
    if WATCHED_SERVICES:
        print(f"[system-monitor] Watching services: {', '.join(WATCHED_SERVICES)}", flush=True)
    else:
        print("[system-monitor] No services configured to watch", flush=True)
    print("[system-monitor] ═══════════════════════════════════════", flush=True)

    # Set up transport
    if TRANSPORT_MODE == "mqtt":
        if not mqtt_connect():
            print("[system-monitor] FATAL: MQTT connection failed. Exiting.", flush=True)
            return
        # Wait for connection to stabilize
        time.sleep(1)
        # Publish MQTT Discovery configs
        register_mqtt_discovery()
    else:
        print(f"[system-monitor] REST API URL: {HA_API_URL}", flush=True)

    # Warm up psutil CPU (first call always returns 0)
    psutil.cpu_percent(percpu=True)
    time.sleep(1)

    cycle = 0
    while True:
        cycle += 1
        start = time.time()

        try:
            publish_cpu()
            publish_memory()
            publish_disks()
            publish_network()
            publish_uptime()
            publish_top_processes()
            publish_host_info()
            publish_services()

            # Temperatures less frequently (every 3rd cycle)
            if cycle % 3 == 1:
                publish_temperatures()

            elapsed = round(time.time() - start, 2)
            if cycle <= 3 or cycle % 60 == 0:
                print(f"[system-monitor] Cycle {cycle} completed in {elapsed}s", flush=True)

        except Exception as e:
            print(f"[system-monitor] Error in cycle {cycle}: {e}", flush=True)

        time.sleep(REFRESH_INTERVAL)


if __name__ == "__main__":
    main()

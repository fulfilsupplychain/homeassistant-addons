#!/usr/bin/env python3
"""
System Monitor — HA Sensor Publisher
Reads system metrics via psutil and publishes them as Home Assistant
sensor entities using the Supervisor API → HA REST API.
"""

import json
import re
import os
import time
import socket
import platform
import urllib.request
import urllib.error

import psutil


# ─── Configuration ──────────────────────────────────────────────────────────────

SUPERVISOR_TOKEN = os.environ.get("SUPERVISOR_TOKEN", "")
HA_API_URL = "http://supervisor/core/api"
REFRESH_INTERVAL = int(os.environ.get("REFRESH_INTERVAL", 5))

HEADERS = {
    "Authorization": f"Bearer {SUPERVISOR_TOKEN}",
    "Content-Type": "application/json",
}

ENTITY_PREFIX = "sensor.system_monitor"


def sanitize_entity_slug(text):
    """Convert text to a valid HA entity ID fragment (lowercase, a-z 0-9 _ only)."""
    slug = text.lower().strip("/")
    slug = re.sub(r'[^a-z0-9]+', '_', slug)  # Replace any non-alphanumeric with _
    slug = slug.strip('_')                    # Remove leading/trailing underscores
    return slug or "unknown"


# ─── API Helper ─────────────────────────────────────────────────────────────────

def post_state(entity_id, state, attributes):
    """Push a sensor entity state to Home Assistant via the Supervisor proxy."""
    url = f"{HA_API_URL}/states/{entity_id}"
    payload = json.dumps({
        "state": state,
        "attributes": attributes,
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers=HEADERS, method="POST")
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


# ─── Metric Collectors ──────────────────────────────────────────────────────────

def publish_cpu():
    """Publish CPU metrics as HA sensors."""
    cpu_pct = psutil.cpu_percent()
    freq = psutil.cpu_freq()
    per_core = psutil.cpu_percent(percpu=True)
    load = list(psutil.getloadavg()) if hasattr(psutil, "getloadavg") else [0, 0, 0]

    # Overall CPU usage
    post_state(f"{ENTITY_PREFIX}_cpu_usage", str(round(cpu_pct, 1)), {
        "friendly_name": "System Monitor CPU Usage",
        "unit_of_measurement": "%",
        "icon": "mdi:cpu-64-bit",
        "device_class": "power_factor",
        "state_class": "measurement",
        "cores_logical": psutil.cpu_count(logical=True),
        "cores_physical": psutil.cpu_count(logical=False),
        "frequency_mhz": round(freq.current, 1) if freq else None,
        "frequency_max_mhz": round(freq.max, 1) if freq else None,
        "load_1m": round(load[0], 2),
        "load_5m": round(load[1], 2),
        "load_15m": round(load[2], 2),
    })

    # CPU frequency
    if freq:
        post_state(f"{ENTITY_PREFIX}_cpu_frequency", str(round(freq.current, 0)), {
            "friendly_name": "System Monitor CPU Frequency",
            "unit_of_measurement": "MHz",
            "icon": "mdi:sine-wave",
            "state_class": "measurement",
            "max_frequency_mhz": round(freq.max, 1) if freq.max else None,
        })

    # Per-core utilization (store as single sensor with attributes)
    core_attrs = {f"core_{i}": round(v, 1) for i, v in enumerate(per_core)}
    core_attrs["friendly_name"] = "System Monitor CPU Cores"
    core_attrs["unit_of_measurement"] = "%"
    core_attrs["icon"] = "mdi:chip"
    core_attrs["core_count"] = len(per_core)
    post_state(f"{ENTITY_PREFIX}_cpu_cores", str(round(cpu_pct, 1)), core_attrs)

    # Load averages
    post_state(f"{ENTITY_PREFIX}_load_1m", str(round(load[0], 2)), {
        "friendly_name": "System Monitor Load 1m",
        "icon": "mdi:gauge",
        "state_class": "measurement",
        "load_5m": round(load[1], 2),
        "load_15m": round(load[2], 2),
    })


def publish_memory():
    """Publish RAM and Swap metrics as HA sensors."""
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    post_state(f"{ENTITY_PREFIX}_ram_usage", str(round(mem.percent, 1)), {
        "friendly_name": "System Monitor RAM Usage",
        "unit_of_measurement": "%",
        "icon": "mdi:memory",
        "state_class": "measurement",
        "total_gb": round(mem.total / (1024**3), 2),
        "used_gb": round(mem.used / (1024**3), 2),
        "available_gb": round(mem.available / (1024**3), 2),
        "total_bytes": mem.total,
        "used_bytes": mem.used,
        "available_bytes": mem.available,
    })

    post_state(f"{ENTITY_PREFIX}_ram_used", str(round(mem.used / (1024**3), 2)), {
        "friendly_name": "System Monitor RAM Used",
        "unit_of_measurement": "GB",
        "icon": "mdi:memory",
        "device_class": "data_size",
        "state_class": "measurement",
    })

    swap_pct = swap.percent if swap.total > 0 else 0
    post_state(f"{ENTITY_PREFIX}_swap_usage", str(round(swap_pct, 1)), {
        "friendly_name": "System Monitor Swap Usage",
        "unit_of_measurement": "%",
        "icon": "mdi:swap-horizontal",
        "state_class": "measurement",
        "total_gb": round(swap.total / (1024**3), 2) if swap.total > 0 else 0,
        "used_gb": round(swap.used / (1024**3), 2) if swap.total > 0 else 0,
        "free_gb": round(swap.free / (1024**3), 2) if swap.total > 0 else 0,
    })


def publish_disks():
    """Publish disk usage metrics as HA sensors."""
    # Skip bind-mounted files (e.g. /etc/resolv.conf) — only real directories
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

        # Sanitize mountpoint for entity_id
        # '/' → 'root', '/config' → 'config', '/mnt/data' → 'mnt_data'
        slug = sanitize_entity_slug(part.mountpoint)
        mount_slug = slug if slug else "root"
        entity_id = f"{ENTITY_PREFIX}_disk_{mount_slug}"

        attrs = {
            "friendly_name": f"System Monitor Disk ({part.mountpoint})",
            "unit_of_measurement": "%",
            "icon": "mdi:harddisk",
            "state_class": "measurement",
            "device": part.device,
            "mountpoint": part.mountpoint,
            "filesystem": part.fstype,
            "total_gb": round(usage.total / (1024**3), 2),
            "used_gb": round(usage.used / (1024**3), 2),
            "free_gb": round(usage.free / (1024**3), 2),
            "total_bytes": usage.total,
            "used_bytes": usage.used,
            "free_bytes": usage.free,
        }

        post_state(entity_id, str(round(usage.percent, 1)), attrs)

        # Track the largest partition for the primary disk sensor
        if usage.total > largest_size:
            largest_size = usage.total
            largest_disk = (usage, attrs)

    # Always publish a 'disk_primary' sensor pointing to the largest partition
    if largest_disk:
        usage, attrs = largest_disk
        primary_attrs = dict(attrs)
        primary_attrs["friendly_name"] = "System Monitor Disk (Primary)"
        post_state(f"{ENTITY_PREFIX}_disk_primary", str(round(usage.percent, 1)), primary_attrs)


def publish_temperatures():
    """Publish temperature sensor readings as HA sensors."""
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
            entity_id = f"{ENTITY_PREFIX}_temp_{label_slug}"

            attrs = {
                "friendly_name": f"System Monitor Temp {label}",
                "unit_of_measurement": "°C",
                "icon": "mdi:thermometer",
                "device_class": "temperature",
                "state_class": "measurement",
                "sensor_group": group_name,
            }
            if sensor.high:
                attrs["high_threshold"] = round(sensor.high, 1)
            if sensor.critical:
                attrs["critical_threshold"] = round(sensor.critical, 1)

            post_state(entity_id, str(round(sensor.current, 1)), attrs)


def publish_network():
    """Publish network I/O metrics as HA sensors."""
    counters = psutil.net_io_counters()

    post_state(f"{ENTITY_PREFIX}_net_sent", str(round(counters.bytes_sent / (1024**2), 1)), {
        "friendly_name": "System Monitor Network Sent",
        "unit_of_measurement": "MB",
        "icon": "mdi:upload-network",
        "device_class": "data_size",
        "state_class": "total_increasing",
        "bytes": counters.bytes_sent,
        "packets": counters.packets_sent,
        "errors": counters.errout,
    })

    post_state(f"{ENTITY_PREFIX}_net_received", str(round(counters.bytes_recv / (1024**2), 1)), {
        "friendly_name": "System Monitor Network Received",
        "unit_of_measurement": "MB",
        "icon": "mdi:download-network",
        "device_class": "data_size",
        "state_class": "total_increasing",
        "bytes": counters.bytes_recv,
        "packets": counters.packets_recv,
        "errors": counters.errin,
    })


def publish_uptime():
    """Publish system uptime as an HA sensor."""
    uptime_secs = round(time.time() - psutil.boot_time())
    days = uptime_secs // 86400
    hours = (uptime_secs % 86400) // 3600
    minutes = (uptime_secs % 3600) // 60

    post_state(f"{ENTITY_PREFIX}_uptime", str(round(uptime_secs / 3600, 1)), {
        "friendly_name": "System Monitor Uptime",
        "unit_of_measurement": "h",
        "icon": "mdi:clock-check-outline",
        "state_class": "total_increasing",
        "days": days,
        "hours": hours,
        "minutes": minutes,
        "uptime_string": f"{days}d {hours}h {minutes}m",
        "boot_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(psutil.boot_time())),
    })


def publish_host_info():
    """Publish static host information as an HA sensor."""
    post_state(f"{ENTITY_PREFIX}_host_info", socket.gethostname(), {
        "friendly_name": "System Monitor Host Info",
        "icon": "mdi:server",
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "cpu_count_physical": psutil.cpu_count(logical=False),
        "cpu_count_logical": psutil.cpu_count(logical=True),
        "ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
    })


def publish_top_processes():
    """Publish top processes as a single sensor with attributes."""
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
        "friendly_name": "System Monitor Top Processes",
        "icon": "mdi:format-list-numbered",
        "total_processes": len(procs),
    }
    for i, p in enumerate(top5):
        attrs[f"process_{i+1}_name"] = p["name"]
        attrs[f"process_{i+1}_pid"] = p["pid"]
        attrs[f"process_{i+1}_cpu"] = p["cpu_percent"]
        attrs[f"process_{i+1}_ram"] = p["memory_percent"]

    post_state(f"{ENTITY_PREFIX}_top_processes", str(len(procs)), attrs)


# ─── Main Loop ──────────────────────────────────────────────────────────────────

def main():
    print("[system-monitor] Starting sensor publisher...", flush=True)
    print(f"[system-monitor] Refresh interval: {REFRESH_INTERVAL}s", flush=True)
    print(f"[system-monitor] HA API URL: {HA_API_URL}", flush=True)

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

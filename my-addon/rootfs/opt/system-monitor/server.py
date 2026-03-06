#!/usr/bin/env python3
"""
System Monitor Dashboard — HTTP Server & API
Serves the web dashboard and provides real-time system metrics via JSON API.
"""

import json
import os
import time
import socket
import platform
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

import psutil


# ─── Configuration ──────────────────────────────────────────────────────────────

PORT = int(os.environ.get("INGRESS_PORT", 8099))
WEB_DIR = Path("/opt/system-monitor/www")
INGRESS_ENTRY = os.environ.get("INGRESS_ENTRY", "")

# ─── Helpers ────────────────────────────────────────────────────────────────────

def get_cpu_info():
    """Gather CPU metrics."""
    freq = psutil.cpu_freq()
    return {
        "percent_per_core": psutil.cpu_percent(percpu=True),
        "percent_total": psutil.cpu_percent(),
        "count_logical": psutil.cpu_count(logical=True),
        "count_physical": psutil.cpu_count(logical=False),
        "freq_current": round(freq.current, 1) if freq else None,
        "freq_max": round(freq.max, 1) if freq else None,
        "load_avg": list(psutil.getloadavg()) if hasattr(psutil, "getloadavg") else None,
    }


def get_memory_info():
    """Gather RAM and Swap metrics."""
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return {
        "ram": {
            "total": mem.total,
            "used": mem.used,
            "available": mem.available,
            "percent": mem.percent,
        },
        "swap": {
            "total": swap.total,
            "used": swap.used,
            "free": swap.free,
            "percent": swap.percent,
        },
    }


def get_disk_info():
    """Gather disk usage for all mounted partitions."""
    disks = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disks.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "fstype": part.fstype,
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent": usage.percent,
            })
        except PermissionError:
            continue
    return disks


def get_temperature_info():
    """Gather temperature sensor readings."""
    temps = {}
    if hasattr(psutil, "sensors_temperatures"):
        try:
            sensor_temps = psutil.sensors_temperatures()
            for name, entries in sensor_temps.items():
                temps[name] = [
                    {
                        "label": e.label or name,
                        "current": round(e.current, 1),
                        "high": round(e.high, 1) if e.high else None,
                        "critical": round(e.critical, 1) if e.critical else None,
                    }
                    for e in entries
                ]
        except Exception:
            pass
    return temps


def get_network_info():
    """Gather network I/O counters."""
    counters = psutil.net_io_counters()
    return {
        "bytes_sent": counters.bytes_sent,
        "bytes_recv": counters.bytes_recv,
        "packets_sent": counters.packets_sent,
        "packets_recv": counters.packets_recv,
        "errin": counters.errin,
        "errout": counters.errout,
    }


def get_top_processes(limit=10):
    """Get the top N processes by CPU usage."""
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
    return procs[:limit]


def get_uptime():
    """Get system uptime in seconds."""
    return round(time.time() - psutil.boot_time())


def get_all_stats():
    """Aggregate all system stats into a single dict."""
    return {
        "timestamp": time.time(),
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "uptime_seconds": get_uptime(),
        "cpu": get_cpu_info(),
        "memory": get_memory_info(),
        "disks": get_disk_info(),
        "temperatures": get_temperature_info(),
        "network": get_network_info(),
        "processes": get_top_processes(10),
    }


# ─── HTTP Handler ───────────────────────────────────────────────────────────────

class MonitorHandler(SimpleHTTPRequestHandler):
    """Custom handler: serves static files + JSON API."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def do_GET(self):
        # Strip ingress prefix if present
        path = self.path
        if INGRESS_ENTRY and path.startswith(INGRESS_ENTRY):
            path = path[len(INGRESS_ENTRY):] or "/"

        # API endpoint
        if path == "/api/stats" or path == "/api/stats/":
            self._send_json(get_all_stats())
            return

        # Health check
        if path == "/api/health" or path == "/api/health/":
            self._send_json({"status": "ok", "uptime": get_uptime()})
            return

        # Serve static files
        self.path = path
        super().do_GET()

    def _send_json(self, data):
        """Send a JSON response."""
        body = json.dumps(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        """Suppress default access logs to keep HA log clean."""
        pass


# ─── Main ───────────────────────────────────────────────────────────────────────

def main():
    # Warm up psutil CPU readings (first call always returns 0)
    psutil.cpu_percent(percpu=True)

    server = HTTPServer(("0.0.0.0", PORT), MonitorHandler)
    print(f"[system-monitor] Dashboard running on port {PORT}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
    print("[system-monitor] Server stopped.", flush=True)


if __name__ == "__main__":
    main()

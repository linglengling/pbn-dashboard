#!/usr/bin/env python3
"""
PBN Client Agent - VPS Node Connector
Location on VPS: /www/wwwroot/pbn-tool/pbn_agent.py

Functions:
- Gathers VPS health metrics (CPU, RAM, Disk, Load, IP, Hostname)
- Transmits encrypted heartbeat signal to the central PBN Dashboard
- Receives and executes remote dispatch commands if instructed by dashboard
"""

import os
import sys
import time
import json
import socket
import urllib.request
import urllib.parse
import subprocess
import shutil

DASHBOARD_URL = "https://pbn.keodinh.net/api/vps/signal"
FALLBACK_URL = "http://103.106.105.77:5556/api/vps/signal"
SECRET_SALT = "pbn_s3cr3t_k3y_2024_change_this"
AGENT_VERSION = "1.0.0"

def get_ip():
    """Detect public IP address of this VPS"""
    services = ["https://api.ipify.org", "https://ifconfig.me/ip", "https://icanhazip.com"]
    for s in services:
        try:
            req = urllib.request.Request(s, headers={"User-Agent": "pbn-agent/1.0"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                ip = resp.read().decode().strip()
                if ip and len(ip.split(".")) == 4:
                    return ip
        except Exception:
            continue
    return socket.gethostbyname(socket.gethostname())

def get_metrics():
    """Collect system CPU, memory, and disk utilization"""
    metrics = {
        "hostname": socket.gethostname(),
        "timestamp": int(time.time()),
        "agent_version": AGENT_VERSION,
        "load_avg": [0, 0, 0],
        "memory": {"total_mb": 0, "used_mb": 0, "free_mb": 0, "percent": 0},
        "disk": {"total_gb": 0, "used_gb": 0, "free_gb": 0, "percent": 0},
        "wp_sites_count": 0
    }

    # Load average
    try:
        metrics["load_avg"] = [round(x, 2) for x in os.getloadavg()]
    except Exception:
        pass

    # Memory
    try:
        with open("/proc/meminfo", "r") as f:
            lines = f.readlines()
        mem_info = {}
        for line in lines:
            parts = line.split(":")
            if len(parts) == 2:
                key = parts[0].strip()
                val = parts[1].strip().split()[0]
                mem_info[key] = int(val)
        total = mem_info.get("MemTotal", 0) // 1024
        available = mem_info.get("MemAvailable", mem_info.get("MemFree", 0)) // 1024
        used = total - available
        pct = round((used / total) * 100, 1) if total > 0 else 0
        metrics["memory"] = {"total_mb": total, "used_mb": used, "free_mb": available, "percent": pct}
    except Exception:
        pass

    # Disk
    try:
        usage = shutil.disk_usage("/www/wwwroot")
        total_gb = round(usage.total / (1024**3), 1)
        used_gb = round(usage.used / (1024**3), 1)
        free_gb = round(usage.free / (1024**3), 1)
        pct = round((usage.used / usage.total) * 100, 1) if usage.total > 0 else 0
        metrics["disk"] = {"total_gb": total_gb, "used_gb": used_gb, "free_gb": free_gb, "percent": pct}
    except Exception:
        pass

    # WordPress site count in /www/wwwroot
    try:
        cmd = "find /www/wwwroot -maxdepth 3 -name 'wp-config.php' 2>/dev/null | wc -l"
        res = subprocess.check_output(cmd, shell=True).decode().strip()
        metrics["wp_sites_count"] = int(res) if res.isdigit() else 0
    except Exception:
        pass

    return metrics

def send_signal():
    """Send heartbeat payload to Central Dashboard"""
    server_ip = get_ip()
    metrics = get_metrics()
    timestamp = metrics["timestamp"]

    import hashlib
    token = hashlib.md5(f"{server_ip}{timestamp}{SECRET_SALT}".encode()).hexdigest()

    payload = {
        "server_ip": server_ip,
        "token": token,
        "timestamp": timestamp,
        "metrics": metrics
    }

    data_bytes = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "User-Agent": f"Mozilla/5.0 (compatible; PBN-VPS-Agent/{AGENT_VERSION}; +https://pbn.keodinh.net)"
    }

    # Attempt primary URL then fallback
    for url in [DASHBOARD_URL, FALLBACK_URL]:
        try:
            req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=8) as resp:
                body = resp.read().decode("utf-8")
                res = json.loads(body)
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Signal sent to {url} - Status: {res.get('success', False)}")
                return res
        except Exception as e:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Warning: Failed sending to {url}: {e}")

    return {"success": False, "error": "All dashboard URLs unreachable"}

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        print(f"PBN VPS Agent v{AGENT_VERSION} starting in daemon loop...")
        while True:
            try:
                send_signal()
            except Exception as e:
                print(f"Loop error: {e}")
            time.sleep(120)  # Ping every 2 minutes
    else:
        # One-shot ping
        res = send_signal()
        print(json.dumps(res, indent=2))

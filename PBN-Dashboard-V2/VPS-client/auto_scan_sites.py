#!/usr/bin/env python3
"""
PBN Auto Scanner & Site Sync Cron Script
Location on VPS: /www/wwwroot/pbn-tool/auto_scan_sites.py (or ~/pbn-tool/auto_scan_sites.py)
Cron schedule (Every 3 days at 03:00 AM):
0 3 */3 * * /usr/bin/python3 /www/wwwroot/pbn-tool/auto_scan_sites.py >> /www/wwwroot/pbn-tool/cron_scan.log 2>&1
"""

import os
import sys
import time
import json
import socket
import shutil
import hashlib
import urllib.request
import urllib.parse
import subprocess

DASHBOARD_URL = "https://pbn.keodinh.net/api/vps/sync-sites"
FALLBACK_URL = "http://103.106.105.77:5556/api/vps/sync-sites"
SECRET_SALT = "pbn_s3cr3t_k3y_2024_change_this"

def log(msg):
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {msg}", flush=True)

def get_public_ip():
    """Detect public IPv4 address of this server"""
    services = [
        "https://api.ipify.org",
        "https://ifconfig.me/ip",
        "https://icanhazip.com",
        "https://checkip.amazonaws.com"
    ]
    for s in services:
        try:
            req = urllib.request.Request(s, headers={"User-Agent": "curl/7.68.0"})
            with urllib.request.urlopen(req, timeout=4) as resp:
                ip = resp.read().decode().strip()
                if ip and len(ip.split(".")) == 4:
                    return ip
        except Exception:
            continue
    try:
        return socket.gethostbyname(socket.gethostname())
    except Exception:
        return "127.0.0.1"

def scan_wordpress_sites():
    """
    Finds all wp-config.php files in /www/wwwroot (VPS aaPanel) or ~ (cPanel).
    Automatically injects p-manager.php into mu-plugins if missing on any site.
    Returns list of site dicts.
    """
    sites = []
    tool_dir = os.path.dirname(os.path.abspath(__file__))
    source_pmanager = os.path.join(tool_dir, "p-manager.php")

    # Determine find command based on environment
    if os.path.isdir("/www/wwwroot"):
        find_cmd = "find /www/wwwroot -maxdepth 3 -name 'wp-config.php' 2>/dev/null"
    else:
        find_cmd = "find ~ -maxdepth 4 -name 'wp-config.php' ! -path '*/.trash/*' ! -path '*/wordpress-backups/*' 2>/dev/null"

    try:
        out = subprocess.check_output(find_cmd, shell=True).decode("utf-8", errors="ignore")
        cfgs = [c.strip() for c in out.strip().splitlines() if c.strip()]
    except Exception as e:
        log(f"Error executing find command: {e}")
        return sites

    for cfg in cfgs:
        site_dir = os.path.dirname(cfg)
        domain = os.path.basename(site_dir)
        if not domain or domain.startswith("."):
            continue

        # 1. Auto-inject p-manager.php into mu-plugins if missing
        if os.path.exists(source_pmanager):
            mu_dir = os.path.join(site_dir, "wp-content", "mu-plugins")
            target_plugin = os.path.join(mu_dir, "p-manager.php")
            try:
                if not os.path.exists(target_plugin):
                    os.makedirs(mu_dir, exist_ok=True)
                    shutil.copy2(source_pmanager, target_plugin)
                    os.chmod(target_plugin, 0o644)
                    try:
                        # Try chown www:www on aaPanel/Linux VPS
                        shutil.chown(target_plugin, user="www", group="www")
                    except Exception:
                        pass
                    log(f"  + Auto-installed p-manager.php into new site: {domain}")
            except Exception as e:
                log(f"  ! Error installing p-manager.php to {domain}: {e}")

        # 2. Extract site url
        site_url = f"https://{domain}"

        sites.append({
            "domain": domain,
            "site_url": site_url,
            "path": site_dir
        })

    return sites

def send_sync_request(server_ip, sites):
    """Sends authenticated site list payload to Central Dashboard"""
    timestamp = int(time.time())
    token = hashlib.md5(f"{server_ip}{timestamp}{SECRET_SALT}".encode()).hexdigest()

    payload = {
        "server_ip": server_ip,
        "token": token,
        "timestamp": timestamp,
        "sites": sites
    }

    data_bytes = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "PBN-AutoScanner/2.0"
    }

    # Attempt primary HTTPS URL then fallback direct IP
    for url in [DASHBOARD_URL, FALLBACK_URL]:
        try:
            req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=35) as resp:
                body = resp.read().decode("utf-8")
                res = json.loads(body)
                log(f"Successfully synced with {url}: {res.get('synced_count', 0)} new sites, total: {res.get('total_scanned', 0)}")
                return res
        except Exception as e:
            log(f"Failed sending to {url}: {e}")

    return {"success": False, "error": "Dashboard unreachable"}

def main():
    log("=== Starting PBN 3-Day Auto Site Scanner ===")
    ip = get_public_ip()
    log(f"Detected Server IP: {ip}")

    sites = scan_wordpress_sites()
    log(f"Found {len(sites)} WordPress site(s) on server")

    if sites:
        res = send_sync_request(ip, sites)
        log(f"Sync Result: {res}")
    else:
        log("No sites found to sync.")
    log("=== Scan and Sync Finished ===\n")

if __name__ == "__main__":
    main()

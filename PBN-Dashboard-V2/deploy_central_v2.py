import os
import sys
import time
import paramiko

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CENTRAL_IP = "103.106.105.77"
CENTRAL_USER = "root"
CENTRAL_PASS = "q9icdLH1!*0B"
CENTRAL_PATH = "/www/wwwroot/pbn-management2.keodinh.net"

LOCAL_BASE = "g:/ProjectDemo/manage-pbn-sites/PBN-Dashboard-V2"

def log(msg):
    clean = str(msg).encode("ascii", errors="replace").decode("ascii")
    print(f"[{time.strftime('%H:%M:%S')}] {clean}", flush=True)

def deploy_central():
    log("Connecting to Central Server 103.106.105.77...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(CENTRAL_IP, username=CENTRAL_USER, password=CENTRAL_PASS, timeout=15)
    sftp = ssh.open_sftp()

    # Upload app files
    log("Uploading app backend files...")
    sftp.put(f"{LOCAL_BASE}/app/database.py", f"{CENTRAL_PATH}/app/database.py")
    sftp.put(f"{LOCAL_BASE}/app/main.py", f"{CENTRAL_PATH}/app/main.py")
    sftp.put(f"{LOCAL_BASE}/app/server_runner.py", f"{CENTRAL_PATH}/app/server_runner.py")
    sftp.put(f"{LOCAL_BASE}/app/audit_runner.py", f"{CENTRAL_PATH}/app/audit_runner.py")
    sftp.put(f"{LOCAL_BASE}/app/routes/audit_routes.py", f"{CENTRAL_PATH}/app/routes/audit_routes.py")
    sftp.put(f"{LOCAL_BASE}/app/routes/vps_routes.py", f"{CENTRAL_PATH}/app/routes/vps_routes.py")
    sftp.put(f"{LOCAL_BASE}/app/routes/clusters_routes.py", f"{CENTRAL_PATH}/app/routes/clusters_routes.py")
    sftp.put(f"{LOCAL_BASE}/app/routes/sites_routes.py", f"{CENTRAL_PATH}/app/routes/sites_routes.py")
    sftp.put(f"{LOCAL_BASE}/app/two_index_service.py", f"{CENTRAL_PATH}/app/two_index_service.py")
    sftp.put(f"{LOCAL_BASE}/app/routes/indexing_routes.py", f"{CENTRAL_PATH}/app/routes/indexing_routes.py")

    # Upload static frontend files
    log("Uploading static frontend assets...")
    try:
        sftp.mkdir(f"{CENTRAL_PATH}/static")
    except Exception:
        pass
    try:
        sftp.mkdir(f"{CENTRAL_PATH}/static/assets")
    except Exception:
        pass

    sftp.put(f"{LOCAL_BASE}/static/index.html", f"{CENTRAL_PATH}/static/index.html")

    local_assets = f"{LOCAL_BASE}/static/assets"
    if os.path.exists(local_assets):
        for fname in os.listdir(local_assets):
            lpath = os.path.join(local_assets, fname)
            if os.path.isfile(lpath):
                sftp.put(lpath, f"{CENTRAL_PATH}/static/assets/{fname}")

    sftp.close()

    # Restart pm2
    log("Restarting PM2 pbn-v2...")
    stdin, stdout, stderr = ssh.exec_command("pm2 restart pbn-v2 && pm2 status")
    res = stdout.read().decode("utf-8", errors="ignore").strip()
    log(f"PM2 status:\n{res}")

    # Ensure 3-day audit cron is in crontab
    log("Checking and updating system crontab for 3-day site error scan...")
    cron_line = "0 3 */3 * * /usr/bin/curl -s -X POST http://127.0.0.1:5556/api/audit/run-scheduled-cron >> /www/wwwroot/pbn-management2.keodinh.net/audit_cron.log 2>&1"
    cmd_cron = f"""
    (crontab -l 2>/dev/null | grep -v 'run-scheduled-cron'; echo '{cron_line}') | crontab -
    """
    stdin, stdout, stderr = ssh.exec_command(cmd_cron)
    stdout.channel.recv_exit_status()
    log("Crontab updated successfully.")

    ssh.close()
    log("Central Server deployment complete!")

if __name__ == "__main__":
    deploy_central()

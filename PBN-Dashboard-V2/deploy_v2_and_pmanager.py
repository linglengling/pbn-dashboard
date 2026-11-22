import os
import sys
import time
import sqlite3
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

def step1_update_central():
    log("=== STEP 1: Updating Central Server (Code + Static + p-manager.php) ===")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(CENTRAL_IP, username=CENTRAL_USER, password=CENTRAL_PASS, timeout=15)
    sftp = ssh.open_sftp()

    # Upload p-manager.php
    log("Uploading p-manager.php & VPS-client/p-manager.php...")
    sftp.put(f"{LOCAL_BASE}/p-manager.php", f"{CENTRAL_PATH}/p-manager.php")
    sftp.put(f"{LOCAL_BASE}/p-manager.php", f"{CENTRAL_PATH}/pbn-manager.php")
    try:
        sftp.mkdir(f"{CENTRAL_PATH}/VPS-client")
    except Exception:
        pass
    sftp.put(f"{LOCAL_BASE}/VPS-client/p-manager.php", f"{CENTRAL_PATH}/VPS-client/p-manager.php")

    # Upload app files
    log("Uploading app backend files...")
    sftp.put(f"{LOCAL_BASE}/app/database.py", f"{CENTRAL_PATH}/app/database.py")
    sftp.put(f"{LOCAL_BASE}/app/audit_runner.py", f"{CENTRAL_PATH}/app/audit_runner.py")
    sftp.put(f"{LOCAL_BASE}/app/routes/audit_routes.py", f"{CENTRAL_PATH}/app/routes/audit_routes.py")
    sftp.put(f"{LOCAL_BASE}/app/routes/sites_routes.py", f"{CENTRAL_PATH}/app/routes/sites_routes.py")

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
    log("Restarting central PM2 process 'pbn-v2'...")
    stdin, stdout, stderr = ssh.exec_command("pm2 restart pbn-v2 && pm2 status")
    res = stdout.read().decode("utf-8", errors="ignore").strip()
    log(f"Central PM2 status:\n{res}")
    ssh.close()
    log("✓ Step 1 Complete!\n")

def get_servers():
    conn = sqlite3.connect(f"{LOCAL_BASE}/pbn_matrix.db")
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM servers WHERE status = 'ONLINE' OR status IS NULL OR status != 'ERROR'").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def step2_deploy_pmanager_all(servers):
    log("=== STEP 2: Deploying p-manager.php to All Client Servers ===")
    p_file = f"{LOCAL_BASE}/p-manager.php"

    for srv in servers:
        host = srv["host"]
        port = srv.get("port") or 22
        user = srv.get("username")
        pwd = srv.get("password")
        name = srv["name"]
        stype = srv.get("type", "vps")

        log(f"Deploying p-manager.php to [{name}] ({host}, {stype})...")
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, port=port, username=user, password=pwd, timeout=15)
            sftp = ssh.open_sftp()

            if stype == "vps":
                remote_tmp = "/tmp/p-manager.php"
                sftp.put(p_file, remote_tmp)
                try:
                    sftp.mkdir("/www/wwwroot/pbn-tool")
                except Exception:
                    pass
                try:
                    sftp.put(p_file, "/www/wwwroot/pbn-tool/p-manager.php")
                except Exception:
                    pass
                sftp.close()

                cmd = """
                find /www/wwwroot -maxdepth 2 -name "wp-config.php" 2>/dev/null | while read cfg; do
                    sdir=$(dirname "$cfg")
                    mdir="$sdir/wp-content/mu-plugins"
                    mkdir -p "$mdir"
                    cp -f /tmp/p-manager.php "$mdir/p-manager.php"
                    chmod 644 "$mdir/p-manager.php"
                    rm -f "$mdir/pbn-manager.php"
                done
                count=$(find /www/wwwroot -maxdepth 4 -name "p-manager.php" 2>/dev/null | wc -l)
                echo "Updated $count sites with p-manager.php"
                """
                stdin, stdout, stderr = ssh.exec_command(cmd)
                out = stdout.read().decode("utf-8", errors="ignore").strip()
                log(f"  ✓ [{name}] {out}")

            else:
                # cPanel
                sftp.put(p_file, "p-manager.php")
                try:
                    sftp.mkdir("pbn-tool")
                except Exception:
                    pass
                try:
                    sftp.put(p_file, "pbn-tool/p-manager.php")
                except Exception:
                    pass
                sftp.close()

                cmd = """
                find ~/public_html ~/domains -maxdepth 3 -name "wp-config.php" 2>/dev/null | while read cfg; do
                    sdir=$(dirname "$cfg")
                    mdir="$sdir/wp-content/mu-plugins"
                    mkdir -p "$mdir"
                    cp -f ~/p-manager.php "$mdir/p-manager.php"
                    chmod 644 "$mdir/p-manager.php"
                    rm -f "$mdir/pbn-manager.php"
                done
                count=$(find ~/public_html ~/domains -maxdepth 5 -name "p-manager.php" 2>/dev/null | wc -l)
                echo "Updated $count sites with p-manager.php"
                """
                stdin, stdout, stderr = ssh.exec_command(cmd)
                out = stdout.read().decode("utf-8", errors="ignore").strip()
                log(f"  ✓ [{name}] {out}")

            ssh.close()
        except Exception as e:
            log(f"  ✗ Failed on [{name}] ({host}): {e}")

    log("✓ Step 2 Complete!\n")

if __name__ == "__main__":
    servers = get_servers()
    step1_update_central()
    step2_deploy_pmanager_all(servers)
    log("🎉 ALL DEPLOYMENTS FINISHED SUCCESSFULLY!")

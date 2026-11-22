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

LOCAL_V2 = "g:/ProjectDemo/manage-pbn-sites/V2"

def log(msg):
    clean = str(msg).encode("ascii", errors="replace").decode("ascii")
    print(f"[{time.strftime('%H:%M:%S')}] {clean}", flush=True)

def step1_update_central():
    log("=== STEP 1: Updating Central Server 103.106.105.77 ===")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(CENTRAL_IP, username=CENTRAL_USER, password=CENTRAL_PASS, timeout=15)
    sftp = ssh.open_sftp()

    log("Uploading p-manager.php to Central Server...")
    sftp.put(f"{LOCAL_V2}/p-manager.php", f"{CENTRAL_PATH}/p-manager.php")
    sftp.put(f"{LOCAL_V2}/p-manager.php", f"{CENTRAL_PATH}/pbn-manager.php")
    sftp.close()

    ssh.exec_command("pm2 restart pbn-v2")
    log("Central PM2 pbn-v2 restarted")
    ssh.close()
    log("✓ Step 1 Complete!\n")

def get_servers():
    conn = sqlite3.connect(f"{LOCAL_V2}/pbn_matrix.db")
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM servers").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def step2_deploy_pmanager_all(servers):
    log("=== STEP 2: Deploying p-manager.php & Removing Old pbn-manager.php across All 10 Servers ===")
    p_file = f"{LOCAL_V2}/p-manager.php"

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
    log("🎉 ALL SERVERS UPDATED WITH p-manager.php!")

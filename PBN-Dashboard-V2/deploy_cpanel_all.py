import paramiko
import sqlite3

conn = sqlite3.connect("V2/pbn_matrix.db")
cpanel_servers = conn.execute("SELECT * FROM servers WHERE type = 'cpanel'").fetchall()
conn.close()

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def log(msg):
    clean = str(msg).encode("ascii", errors="replace").decode("ascii")
    print(clean, flush=True)

for srv in cpanel_servers:
    host = srv[3]
    user = srv[5]
    pwd = srv[6]
    name = srv[1]
    log(f"\nDeploying to [{name}] ({host}, {user})...")

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=user, password=pwd, timeout=20)
        sftp = ssh.open_sftp()
        sftp.put("V2/p-manager.php", "p-manager.php")
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
        echo "Updated $count sites with p-manager.php on $HOSTNAME"
        """
        stdin, stdout, stderr = ssh.exec_command(cmd)
        out = stdout.read().decode('utf-8', errors='ignore').strip()
        log(f"  OK: {out}")
        ssh.close()
    except Exception as e:
        log(f"  FAILED on [{name}]: {e}")

log("\nDone deploying to all cPanel servers!")

import paramiko
import sqlite3

conn = sqlite3.connect("V2/pbn_matrix.db")
tor = conn.execute("SELECT * FROM servers WHERE host LIKE '%tor%'").fetchone()
conn.close()

host = tor[3]
user = tor[5]
pwd = tor[6]
print(f"Connecting to {host} as {user}...")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=pwd, timeout=15)
sftp = ssh.open_sftp()
sftp.put("V2/p-manager.php", "p-manager.php")
sftp.close()

cmd = """
find ~/public_html -maxdepth 3 -name "wp-config.php" 2>/dev/null | while read cfg; do
    sdir=$(dirname "$cfg")
    mdir="$sdir/wp-content/mu-plugins"
    mkdir -p "$mdir"
    cp -f ~/p-manager.php "$mdir/p-manager.php"
    chmod 644 "$mdir/p-manager.php"
    rm -f "$mdir/pbn-manager.php"
done
count=$(find ~/public_html -maxdepth 5 -name "p-manager.php" 2>/dev/null | wc -l)
echo "cPanel TOR updated $count sites with p-manager.php"
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
ssh.close()

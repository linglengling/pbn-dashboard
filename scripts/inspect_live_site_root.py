import sqlite3
import paramiko

conn = sqlite3.connect('PBN-Dashboard-V2/pbn_matrix.db')
srv = conn.execute("SELECT host, username, password FROM servers WHERE host LIKE '%sng%' LIMIT 1").fetchone()
conn.close()

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(srv[0], username=srv[1], password=srv[2], timeout=15)

cmd = """
echo "=== LIST ROOT OF 1 SITE ==="
ls -la /home2/mseocom2/domains/hd88day | head -n 35

echo "=== CHECK index.php CONTENT ==="
head -n 25 /home2/mseocom2/domains/hd88day/index.php

echo "=== CHECK mu-plugins OF SITE ==="
ls -la /home2/mseocom2/domains/hd88day/wp-content/mu-plugins 2>/dev/null

echo "=== CHECK MALWARE QUARANTINE DIR ==="
ls -la /home2/mseocom2/domains/hd88day/wp-content/malware/root 2>/dev/null || echo "No malware dir"
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
ssh.close()


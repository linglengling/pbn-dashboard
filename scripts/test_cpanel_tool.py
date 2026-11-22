import sqlite3
import paramiko

conn = sqlite3.connect('PBN-Dashboard-V2/pbn_matrix.db')
cur = conn.cursor()
cur.execute("SELECT id, name, type, host, username, password FROM servers WHERE type = 'cpanel' LIMIT 1")
srv = cur.fetchone()
conn.close()

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(srv[3], username=srv[4], password=srv[5], timeout=15)

cmd = """
ls -la ~/pbn-tool
echo "--- CHATTR TEST ---"
touch /tmp/test_attr && chattr +i /tmp/test_attr 2>&1 || echo "chattr failed as expected for non-root"
rm -f /tmp/test_attr 2>/dev/null
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
ssh.close()


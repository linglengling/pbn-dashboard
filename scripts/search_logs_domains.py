import paramiko
import sys

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import sqlite3

conn = sqlite3.connect('/www/server/panel/data/default.db')
cur = conn.cursor()
cur.execute("SELECT id, type, log, addtime FROM logs WHERE log LIKE '%anthony%' OR log LIKE '%aaidudec%' OR log LIKE '%bblatin%' ORDER BY id ASC")
for r in cur.fetchall():
    print(r)
conn.close()
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)

sftp = ssh.open_sftp()
with sftp.file('/tmp/search_logs_domains.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/search_logs_domains.py')
sys.stdout.reconfigure(encoding='utf-8')
print("STDOUT:\n", stdout.read().decode('utf-8', errors='ignore'))
ssh.close()


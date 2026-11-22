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
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("Tables:", cur.fetchall())

try:
    cur.execute("SELECT id, type, name, filename, addtime FROM backup")
    rows = cur.fetchall()
    print("Backups:", rows)
except Exception as e:
    print("Backup err:", e)

try:
    cur.execute("SELECT id, type, log, addtime FROM logs ORDER BY id DESC LIMIT 50")
    logs = cur.fetchall()
    print("Logs:")
    for l in logs:
        print(l)
except Exception as e:
    print("Logs err:", e)
conn.close()
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_aapanel.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/check_aapanel.py')
sys.stdout.reconfigure(encoding='utf-8')
print(stdout.read().decode('utf-8', errors='ignore'))
ssh.close()


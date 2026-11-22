import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = '''
import sqlite3

conn = sqlite3.connect('/www/server/panel/data/default.db')
cur = conn.cursor()

# Get all databases
cur.execute("SELECT name FROM databases")
db_names = [r[0] for r in cur.fetchall()]

print(f"Total DBs in aaPanel: {len(db_names)}")
for db in sorted(db_names):
    # Match by name in backup table
    cur.execute("SELECT name, filename, addtime, size FROM backup WHERE type=1 AND name LIKE ? ORDER BY addtime ASC", (f"%{db}%",))
    rows = cur.fetchall()
    dates = [r[2][:10] for r in rows]
    print(f"[{db}]: {len(rows)} backups -> {dates}")
    for r in rows:
        if '2026-10-31' not in r[2]:
            print(f"    {r[2]} | {r[0]} | {r[1]} ({r[3]} bytes)")

conn.close()
'''

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
sftp = ssh.open_sftp()
with sftp.file('/tmp/check_db_names.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/check_db_names.py')
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
print('STDERR:\n', stderr.read().decode('utf-8', errors='ignore'))
ssh.close()

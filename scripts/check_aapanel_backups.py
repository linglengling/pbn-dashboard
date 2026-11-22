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

cur.execute("SELECT id, type, name, filename, addtime, size FROM backup WHERE type=1 ORDER BY addtime DESC")
rows = cur.fetchall()
print(f"TOTAL DB BACKUP ENTRIES: {len(rows)}")
dates = set()
for r in rows:
    dates.add(r[4][:10])

print("Dates with DB backups:", sorted(list(dates)))

for dt in sorted(list(dates)):
    count = sum(1 for r in rows if r[4].startswith(dt))
    print(f"Date {dt}: {count} DB backups")

print("\\nSample entries from 2026-10-26:")
for r in rows:
    if r[4].startswith('2026-10-26'):
        print(" ", r[2], r[3], r[4], r[5])

print("\\nSample entries from 2026-10-21:")
for r in rows:
    if r[4].startswith('2026-10-21'):
        print(" ", r[2], r[3], r[4], r[5])

print("\\nSample entries from 2026-10-11:")
for r in rows:
    if r[4].startswith('2026-10-11'):
        print(" ", r[2], r[3], r[4], r[5])

conn.close()
'''

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
sftp = ssh.open_sftp()
with sftp.file('/tmp/check_db_backups.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/check_db_backups.py')
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
print('STDERR:\n', stderr.read().decode('utf-8', errors='ignore'))
ssh.close()

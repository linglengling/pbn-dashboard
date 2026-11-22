import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = '''
import sqlite3, os, subprocess

conn = sqlite3.connect('/www/server/panel/data/default.db')
cur = conn.cursor()

cur.execute("SELECT id, type, name, filename, addtime, size FROM backup WHERE name LIKE '%votranh%' OR name LIKE '%vt2%' ORDER BY addtime DESC")
print("BACKUP TABLE for votranh/vt2:")
for r in cur.fetchall():
    print(" ", r)

conn.close()

# Check local backups on disk
p = subprocess.run("find /www/backup -name '*votranh*' -o -name '*vt2*'", shell=True, capture_output=True, text=True)
print("\\nLOCAL BACKUP FILES:")
print(p.stdout)
'''

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
sftp = ssh.open_sftp()
with sftp.file('/tmp/check_votranh_backups.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/check_votranh_backups.py')
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
print('STDERR:\n', stderr.read().decode('utf-8', errors='ignore'))
ssh.close()


import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import os, subprocess

cmd = '''
find /root /home /var/backup* /www/backup* /tmp -type f \\( -name "*.sql*" -o -name "*.wpress" -o -name "*.tar.gz" -o -name "*.zip" \\) 2>/dev/null
'''
p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
lines = p.stdout.strip().splitlines()

# Filter and print
for l in lines:
    if any(k in l.lower() for k in ['aaidudec', 'anthony', 'bblatin', 'conade', 'factura', 'greatdriving', 'hkhoe', 'sburl', 'shadow', 'smv', 'snow', 'stepl', 'suzanne', 'thaiasia', 'feshun', 'hellbender', 'innkeeper', 'rogalevich', 'j-core', 'kvdeveloper', 'benscar', 'kyle', 'respect', 'sougi', 'pbn', 'db_', 'wp_']):
        size = os.path.getsize(l)
        mtime = os.path.getmtime(l)
        import datetime
        dt = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
        print(f"{l:80s} | {size/1024:9.1f} KB | {dt}")
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
sftp = ssh.open_sftp()
with sftp.file('/tmp/find_all_older_backups.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/find_all_older_backups.py')
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
print('STDERR:\n', stderr.read().decode('utf-8', errors='ignore'))
ssh.close()


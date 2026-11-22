import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = '''
import os, sys, time

# 1. First make a quick backup of current vt2 directory before anything
print("Step 1: Backing up current /www/wwwroot/vt2.com state...")
os.makedirs("/www/backup/vt2_pre_restore", exist_ok=True)
os.system("tar -czf /www/backup/vt2_pre_restore/vt2_current_backup.tar.gz -C /www/wwwroot vt2.com")
print("Pre-restore backup created.")

# 2. Download from Google Drive using gdrive plugin
print("\\nStep 2: Downloading web_vt2.com_20261031_004812_4ufAxC.tar.gz from Google Drive...")
sys.path.append('/www/server/panel/plugin/gdrive')
import gdrive_main

c = gdrive_main.gdrive_main()
c.set_creds()

filename = "web_vt2.com_20261031_004812_4ufAxC.tar.gz"
c.download_file(filename)

target_path = f"/tmp/{filename}"
if os.path.exists(target_path):
    print(f"Downloaded successfully: {target_path} ({os.path.getsize(target_path)} bytes)")
else:
    print(f"File not found at {target_path}")
'''

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
sftp = ssh.open_sftp()
with sftp.file('/tmp/download_vt2_backup.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('/www/server/panel/pyenv/bin/python3 /tmp/download_vt2_backup.py')
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
print('STDERR:\n', stderr.read().decode('utf-8', errors='ignore'))
ssh.close()


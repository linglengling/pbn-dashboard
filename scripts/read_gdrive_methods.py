import paramiko
import sys

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
with open('/www/server/panel/plugin/gdrive/gdrive_main.py', 'r') as f:
    code = f.read()

import re
print("Matches for list/get in gdrive_main.py:")
for line in code.splitlines():
    if any(k in line.lower() for k in ['def ', 'files().list', 'drive.files']):
        print(line)
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)

sftp = ssh.open_sftp()
with sftp.file('/tmp/read_gdrive_methods.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/read_gdrive_methods.py')
sys.stdout.reconfigure(encoding='utf-8')
print("STDOUT:\n", stdout.read().decode('utf-8', errors='ignore'))
ssh.close()


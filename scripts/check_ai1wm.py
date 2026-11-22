import paramiko
import sys

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import os, subprocess

cmd = "find /www -name '*ai1wm-backups*' -o -name '*.wpress' 2>/dev/null"
p = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, text=True)
print(p.stdout)
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_ai1wm.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/check_ai1wm.py')
sys.stdout.reconfigure(encoding='utf-8')
print("STDOUT:\n", stdout.read().decode('utf-8', errors='ignore'))
ssh.close()


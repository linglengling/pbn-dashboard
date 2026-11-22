import paramiko
import sys

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import os, subprocess

cmd = "ls -lat /www/wwwroot/anthonyruivivar.net /www/wwwroot/aaidudec.org"
p = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, text=True)
print(p.stdout)
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_logs.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/check_logs.py')
sys.stdout.reconfigure(encoding='utf-8')
print(stdout.read().decode('utf-8', errors='ignore'))
ssh.close()

import paramiko
import sys

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import os, subprocess

p = subprocess.run("pidof mysqld", shell=True, stdout=subprocess.PIPE, text=True)
pid = p.stdout.strip()
print("mysqld PID:", pid)
if pid:
    p2 = subprocess.run(f"ls -l /proc/{pid}/fd 2>/dev/null | grep deleted", shell=True, stdout=subprocess.PIPE, text=True)
    print("Deleted FDs:", p2.stdout)
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)

sftp = ssh.open_sftp()
with sftp.file('/tmp/inspect_dumps.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/inspect_dumps.py')
sys.stdout.reconfigure(encoding='utf-8')
print("STDOUT:\n", stdout.read().decode('utf-8', errors='ignore'))
ssh.close()

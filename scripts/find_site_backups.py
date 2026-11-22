import paramiko
import sys

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import os, subprocess, json

with open('/tmp/site_configs.json', 'r') as f:
    configs = json.load(f)

for c in configs:
    d = c['domain']
    path = f"/www/wwwroot/{d}"
    if os.path.exists(path):
        p = subprocess.run(f"find {path} -name '*.sql*' -o -name '*.wpress' -o -name '*backup*' 2>/dev/null", shell=True, stdout=subprocess.PIPE, text=True)
        lines = [l for l in p.stdout.splitlines() if not 'node_modules' in l and not 'cache' in l]
        if lines:
            print(f"=== {d} ===")
            for l in lines:
                print(" ", l)
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)

sftp = ssh.open_sftp()
with sftp.file('/tmp/find_site_backups.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/find_site_backups.py')
sys.stdout.reconfigure(encoding='utf-8')
print("STDOUT:\n", stdout.read().decode('utf-8', errors='ignore'))
ssh.close()


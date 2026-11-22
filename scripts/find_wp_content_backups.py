import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import os, subprocess, json

with open('/tmp/site_configs.json', 'r') as f:
    configs = json.load(f)

print("=== CHECKING FOR BACKUPS IN WP-CONTENT ===")
for c in configs:
    d = c['domain']
    p = f"/www/wwwroot/{d}/wp-content"
    if os.path.exists(p):
        cmd = f"find {p} -maxdepth 3 \\( -name '*.sql*' -o -name '*.wpress' -o -name '*backup*' \\) 2>/dev/null"
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()
        lines = [l for l in res.splitlines() if not 'cache' in l]
        if lines:
            print(f"[{d}]")
            for l in lines:
                size = os.path.getsize(l) if os.path.isfile(l) else 0
                print(f"  {l} ({size/1024:.1f} KB)")
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
sftp = ssh.open_sftp()
with sftp.file('/tmp/find_wp_content_backups.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/find_wp_content_backups.py')
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
print('STDERR:\n', stderr.read().decode('utf-8', errors='ignore'))
ssh.close()


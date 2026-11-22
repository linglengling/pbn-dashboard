import paramiko
import json
import sys

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import json, subprocess

with open('/tmp/site_configs.json', 'r') as f:
    configs = json.load(f)

for c in configs:
    domain = c['domain']
    path = f"/www/wwwroot/{domain}"
    subprocess.run(["wp", "litespeed-purge", "all", f"--path={path}", "--allow-root"], capture_output=True)

subprocess.run("rm -rf /usr/local/lsws/cachedata/priv/*", shell=True)
subprocess.run("/usr/local/lsws/bin/lswsctrl reload", shell=True)
print("All caches purged and LSWS reloaded.")
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)

sftp = ssh.open_sftp()
with sftp.file('/tmp/purge_all_lscache.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/purge_all_lscache.py')
sys.stdout.reconfigure(encoding='utf-8')
print("STDOUT:\n", stdout.read().decode('utf-8', errors='ignore'))
ssh.close()


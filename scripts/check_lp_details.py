import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = '''
import os, subprocess

lp_path = "/www/wwwroot/vt2.com/wp-content/plugins/learnpress"
print("Learnpress path exists:", os.path.exists(lp_path))

inc_cache = os.path.join(lp_path, "inc/cache")
print("inc/cache exists:", os.path.exists(inc_cache))
if os.path.exists(inc_cache):
    print("Files in inc/cache:", os.listdir(inc_cache))
else:
    print("Files in inc:", os.listdir(os.path.join(lp_path, "inc")) if os.path.exists(os.path.join(lp_path, "inc")) else "inc missing")

# Check learnpress version or plugin status
cmd = "wp --path=/www/wwwroot/vt2.com plugin list --allow-root --skip-plugins=learnpress"
p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
print("PLUGIN LIST (skipping learnpress):")
print(p.stdout)
'''

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
sftp = ssh.open_sftp()
with sftp.file('/tmp/check_lp_details.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/check_lp_details.py')
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
print('STDERR:\n', stderr.read().decode('utf-8', errors='ignore'))
ssh.close()


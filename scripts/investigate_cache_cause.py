import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = '''
import subprocess

print("=== 1. Check all bash histories ===")
p = subprocess.run("grep -iE 'cache|clear|rm -r|clean' /root/.bash_history /home/*/.bash_history 2>/dev/null | tail -n 40", shell=True, capture_output=True, text=True)
print(p.stdout)

print("=== 2. Check aaPanel logs for any execution ===")
p = subprocess.run("grep -iE 'cache' /www/server/panel/logs/*.log 2>/dev/null | tail -n 30", shell=True, capture_output=True, text=True)
print(p.stdout)

print("=== 3. Check for any shell or python scripts in /root, /tmp, /www containing 'cache' ===")
p = subprocess.run("grep -rn 'rm -rf.*cache' /root /www/wwwroot/pbn-management* /www/server/cron 2>/dev/null", shell=True, capture_output=True, text=True)
print(p.stdout)
'''

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
sftp = ssh.open_sftp()
with sftp.file('/tmp/investigate_cache_cause.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/investigate_cache_cause.py')
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
print('STDERR:\n', stderr.read().decode('utf-8', errors='ignore'))
ssh.close()


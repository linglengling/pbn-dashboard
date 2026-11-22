import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = '''
import subprocess

# Check cron logs in /www/server/cron/
print("--- Check cron log files mtime around 02:30-02:40 ---")
p = subprocess.run("find /www/server/cron -name '*.log' -mtime -1 -exec ls -lt {} +", shell=True, capture_output=True, text=True)
print(p.stdout[:1000])

# Check what each cron script does
p2 = subprocess.run("grep -rn 'rm -rf' /www/server/cron/ 2>/dev/null", shell=True, capture_output=True, text=True)
print("Cron scripts with rm -rf:")
print(p2.stdout)

# Check panel task logs
p3 = subprocess.run("tail -n 50 /www/server/panel/logs/task.log 2>/dev/null", shell=True, capture_output=True, text=True)
print("Panel task.log:")
print(p3.stdout)
'''

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
sftp = ssh.open_sftp()
with sftp.file('/tmp/check_0235.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/check_0235.py')
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
print('STDERR:\n', stderr.read().decode('utf-8', errors='ignore'))
ssh.close()


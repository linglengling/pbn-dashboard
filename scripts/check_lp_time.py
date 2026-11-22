import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = '''
import subprocess

p = subprocess.run("ls -la /www/wwwroot/vt2.com/wp-content/plugins/learnpress/learnpress.php", shell=True, capture_output=True, text=True)
print("learnpress.php stat:", p.stdout)

# Check recent modified files in learnpress
p = subprocess.run("find /www/wwwroot/vt2.com/wp-content/plugins/learnpress -type f -mtime -30", shell=True, capture_output=True, text=True)
print("Recently modified files in learnpress:", p.stdout)
'''

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
sftp = ssh.open_sftp()
with sftp.file('/tmp/check_lp_time.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/check_lp_time.py')
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
print('STDERR:\n', stderr.read().decode('utf-8', errors='ignore'))
ssh.close()


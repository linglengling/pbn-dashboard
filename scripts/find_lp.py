import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = '''
import subprocess

p = subprocess.run("find /www -name 'class-lp-cache.php' 2>/dev/null", shell=True, capture_output=True, text=True)
print("Find class-lp-cache.php:")
print(p.stdout)

# Check if there is another learnpress on the server
p2 = subprocess.run("find /www/wwwroot -type d -name 'learnpress' 2>/dev/null", shell=True, capture_output=True, text=True)
print("Learnpress dirs on server:")
print(p2.stdout)
'''

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
sftp = ssh.open_sftp()
with sftp.file('/tmp/find_lp.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/find_lp.py')
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
print('STDERR:\n', stderr.read().decode('utf-8', errors='ignore'))
ssh.close()


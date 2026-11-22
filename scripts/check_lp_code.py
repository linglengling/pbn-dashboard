import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = '''
with open('/www/wwwroot/vt2.com/wp-content/plugins/learnpress/learnpress.php', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

for i in range(250, min(300, len(lines))):
    print(f"{i+1}: {lines[i]}", end='')

# Check file header
print("\\n--- HEADER ---")
for i in range(min(30, len(lines))):
    print(f"{i+1}: {lines[i]}", end='')
'''

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
sftp = ssh.open_sftp()
with sftp.file('/tmp/check_lp_code.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/check_lp_code.py')
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
print('STDERR:\n', stderr.read().decode('utf-8', errors='ignore'))
ssh.close()


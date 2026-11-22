import paramiko

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)

cmd = '''
python3 -c "
import os
if os.path.exists('/root/.bash_history'):
    with open('/root/.bash_history', 'r', errors='ignore') as f:
        lines = f.readlines()
    for l in lines[-150:]:
        print(l.strip())
"
'''
stdin, stdout, stderr = ssh.exec_command(cmd)
import sys
sys.stdout.reconfigure(encoding='utf-8')
print(stdout.read().decode('utf-8', errors='ignore'))
ssh.close()

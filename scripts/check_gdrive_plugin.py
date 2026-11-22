import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = '''
import os

print("Files in /www/server/panel/plugin/gdrive/:")
if os.path.exists('/www/server/panel/plugin/gdrive'):
    for f in os.listdir('/www/server/panel/plugin/gdrive'):
        print(" ", f)

# Check if there is a download script or client
# Let's inspect gdrive_main.py
if os.path.exists('/www/server/panel/plugin/gdrive/gdrive_main.py'):
    with open('/www/server/panel/plugin/gdrive/gdrive_main.py', 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        print("gdrive_main.py size:", len(content))
        # Look for download functions
        for line in content.splitlines():
            if 'def ' in line or 'download' in line.lower():
                print("   ", line)
'''

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
sftp = ssh.open_sftp()
with sftp.file('/tmp/check_gdrive_plugin.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/check_gdrive_plugin.py')
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
print('STDERR:\n', stderr.read().decode('utf-8', errors='ignore'))
ssh.close()


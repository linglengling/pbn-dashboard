import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = '''
with open('/www/server/panel/plugin/gdrive/gdrive_main.py', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

in_func = False
for idx, line in enumerate(lines):
    if 'def download_file' in line or 'def _get_file_id' in line:
        in_func = True
        print(f"--- LINE {idx} ---")
    if in_func:
        print(line, end='')
        if line.strip().startswith('def ') and not ('download_file' in line or '_get_file_id' in line):
            in_func = False
'''

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
sftp = ssh.open_sftp()
with sftp.file('/tmp/inspect_gdrive_funcs.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/inspect_gdrive_funcs.py')
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
print('STDERR:\n', stderr.read().decode('utf-8', errors='ignore'))
ssh.close()


import paramiko
import sys

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import sys
sys.path.append('/www/server/panel/plugin/gdrive')
try:
    import gdrive_main
    client = gdrive_main.gdrive_main()
    print("Methods:", [m for m in dir(client) if not m.startswith('__')])
    # Try get list
    res = client.get_list('/backup_path/database/mysql')
    print("Result get_list:", res)
except Exception as e:
    import traceback
    traceback.print_exc()
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)

sftp = ssh.open_sftp()
with sftp.file('/tmp/test_gdrive_list.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('/www/server/panel/pyenv/bin/python3 /tmp/test_gdrive_list.py')
sys.stdout.reconfigure(encoding='utf-8')
print("STDOUT:\n", stdout.read().decode('utf-8', errors='ignore'))
print("STDERR:\n", stderr.read().decode('utf-8', errors='ignore'))
ssh.close()

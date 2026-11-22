import paramiko
import sys

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import sys
sys.path.append('/www/server/panel/plugin/gdrive')
import gdrive_main

client = gdrive_main.gdrive_main()
service = client._check_connect()
if not service:
    print("Failed to connect to Google Drive service")
else:
    print("Connected to Google Drive successfully!")
    results = service.files().list(pageSize=100, fields="nextPageToken, files(id, name, mimeType, modifiedTime, size)").execute()
    files = results.get('files', [])
    print(f"Total files returned: {len(files)}")
    for f in files:
        print(f"{f.get('name')} | {f.get('modifiedTime')} | {f.get('size')} bytes")
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)

sftp = ssh.open_sftp()
with sftp.file('/tmp/search_gdrive.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('/www/server/panel/pyenv/bin/python3 /tmp/search_gdrive.py')
sys.stdout.reconfigure(encoding='utf-8')
print("STDOUT:\n", stdout.read().decode('utf-8', errors='ignore'))
print("STDERR:\n", stderr.read().decode('utf-8', errors='ignore'))
ssh.close()


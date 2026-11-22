import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import sys
sys.path.append('/www/server/panel/plugin/gdrive')
from googleapiclient.discovery import build
import gdrive_main

c = gdrive_main.gdrive_main()
c.set_creds()
service = build('drive', 'v3', credentials=c._gdrive_main__creds)

# Search for all files with name containing 'sql' or 'db_'
query = "name contains 'sql' or name contains 'db_' or name contains 'aaidudec' or name contains 'anthony'"
page_token = None
all_files = []

while True:
    results = service.files().list(
        q=query,
        pageSize=100,
        fields="nextPageToken, files(id, name, mimeType, modifiedTime, size)",
        pageToken=page_token
    ).execute()
    files = results.get('files', [])
    all_files.extend(files)
    page_token = results.get('nextPageToken')
    if not page_token:
        break

print(f"Total matching files found on Google Drive: {len(all_files)}")
# Sort by name and modifiedTime
for f in sorted(all_files, key=lambda x: (x.get('name', ''), x.get('modifiedTime', ''))):
    print(f"  {f.get('name')} | {f.get('size')} bytes | modified: {f.get('modifiedTime')} | id: {f.get('id')}")
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
sftp = ssh.open_sftp()
with sftp.file('/tmp/search_gdrive_backups.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('/www/server/panel/pyenv/bin/python3 /tmp/search_gdrive_backups.py')
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
print('STDERR:\n', stderr.read().decode('utf-8', errors='ignore'))
ssh.close()

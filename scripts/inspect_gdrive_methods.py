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
try:
    from googleapiclient.discovery import build
    import gdrive_main

    c = gdrive_main.gdrive_main()
    print("set_creds:", c.set_creds())
    service = build('drive', 'v3', credentials=c._gdrive_main__creds)
    results = service.files().list(pageSize=50, fields="files(id, name, mimeType, modifiedTime, size)").execute()
    files = results.get('files', [])
    print(f"Total files returned without query: {len(files)}")
    for f in files[:20]:
        print(f"  {f.get('name')} | {f.get('modifiedTime')}")
except Exception as e:
    import traceback
    traceback.print_exc()
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
sftp = ssh.open_sftp()
with sftp.file('/tmp/test_gdrive_list2.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('/www/server/panel/pyenv/bin/python3 /tmp/test_gdrive_list2.py')
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
print('STDERR:\n', stderr.read().decode('utf-8', errors='ignore'))
ssh.close()

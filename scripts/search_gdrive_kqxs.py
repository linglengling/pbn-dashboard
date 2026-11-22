import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=15)

cmd = """python3 -c "
import json
from googleapiclient.discovery import build
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials

with open('/www/server/panel/plugin/gdrive/credentials.json') as f:
    conf = json.load(f)

creds = Credentials(
    None,
    refresh_token=conf['refresh_token'],
    token_uri='https://oauth2.googleapis.com/token',
    client_id=conf['client_id'],
    client_secret=conf['client_secret']
)

service = build('drive', 'v3', credentials=creds)

results = service.files().list(
    q=\"name contains 'kqsx' or name contains 'kqxs' or name contains 'wp-optimize'\",
    pageSize=30,
    fields='files(id, name, size, modifiedTime)'
).execute()

for f in results.get('files', []):
    size_mb = int(f.get('size', 0)) / 1024 / 1024
    print(f'{f[\"name\"]} | {size_mb:.2f} MB | {f.get(\"modifiedTime\")}')
"
"""

stdin, stdout, stderr = ssh.exec_command(cmd)
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
print('STDERR:\n', stderr.read().decode('utf-8', errors='ignore'))
ssh.close()


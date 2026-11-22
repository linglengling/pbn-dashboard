import sys
sys.path.append('/www/server/panel/plugin/gdrive')
from googleapiclient.discovery import build
import gdrive_main

c = gdrive_main.gdrive_main()
c.set_creds()
service = build('drive', 'v3', credentials=c._gdrive_main__creds)

results = service.files().list(
    q="'1v3yY_2c53nffAQDLbKS3XpzhKXwu9I0w' in parents",
    pageSize=50,
    fields="files(id, name, mimeType, modifiedTime, size)"
).execute()

print(f"Files in kqsxmientrung.com folder: {len(results.get('files', []))}")
for f in results.get('files', []):
    size_mb = int(f.get('size', 0)) / 1024 / 1024
    print(f"{f.get('name')} | {size_mb:.2f} MB | {f.get('modifiedTime')} | id: {f.get('id')}")

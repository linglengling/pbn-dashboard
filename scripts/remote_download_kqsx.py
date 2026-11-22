import os
import sys
import time

sys.path.append('/www/server/panel/plugin/gdrive')
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import gdrive_main

print("Step 0: Backing up current /www/wwwroot/kqsxmientrung.com...")
os.makedirs("/www/backup/kqsx_pre_restore", exist_ok=True)
os.system("tar -czf /www/backup/kqsx_pre_restore/kqsx_current_backup.tar.gz -C /www/wwwroot kqsxmientrung.com/wp-content/plugins")
print("Pre-restore backup of plugins created.")

filename = "web_kqsxmientrung.com_20261031_003951_A0bIHr.tar.gz"
file_id = "1aDJFT5Q0jJcZKyTRi6SIDGxGyKO8UO-j"
target_path = f"/tmp/{filename}"

print(f"Step 1: Downloading {filename} from Google Drive...")

c = gdrive_main.gdrive_main()
c.set_creds()
service = build('drive', 'v3', credentials=c._gdrive_main__creds)
request = service.files().get_media(fileId=file_id)

chunk_size = 50 * 1024 * 1024 # 50 MB chunk

with open(target_path, 'wb') as fh:
    downloader = MediaIoBaseDownload(fh, request, chunksize=chunk_size)
    done = False
    start_time = time.time()
    while not done:
        status, done = downloader.next_chunk()
        pct = int(status.progress() * 100)
        elapsed = time.time() - start_time
        mb = fh.tell() / 1024 / 1024
        speed = mb / elapsed if elapsed > 0 else 0
        print(f"Progress: {pct}% ({mb:.1f} MB, {speed:.1f} MB/s)")

print(f"Download completed in {time.time() - start_time:.1f}s: {target_path} ({os.path.getsize(target_path)} bytes)")

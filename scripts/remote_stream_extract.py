import sys
import os
import subprocess
import time
sys.path.append('/www/server/panel/plugin/gdrive')
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import gdrive_main
import io

os.makedirs('/tmp/kqsx_extract', exist_ok=True)

c = gdrive_main.gdrive_main()
c.set_creds()
service = build('drive', 'v3', credentials=c._gdrive_main__creds)

file_id = '1aDJFT5Q0jJcZKyTRi6SIDGxGyKO8UO-j'
request = service.files().get_media(fileId=file_id)

print("Starting streaming extraction of wp-optimize plugins...")
tar_proc = subprocess.Popen(
    ['tar', '-xzvf', '-', '-C', '/tmp/kqsx_extract', '--wildcards', '*wp-optimize*'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

chunk_size = 10 * 1024 * 1024 # 10MB chunks
downloader = MediaIoBaseDownload(io.BytesIO(), request, chunksize=chunk_size)

done = False
bytes_read = 0

while not done:
    fh = io.BytesIO()
    downloader._fh = fh
    status, done = downloader.next_chunk()
    chunk_bytes = fh.getvalue()
    bytes_read += len(chunk_bytes)
    print(f"Downloaded {bytes_read / 1024 / 1024:.1f} MB...")
    
    try:
        tar_proc.stdin.write(chunk_bytes)
        tar_proc.stdin.flush()
    except BrokenPipeError:
        print("Tar finished or broken pipe.")
        break
        
    # Check if we already have cache in both wp-optimize and wp-optimize-premium
    p1 = '/tmp/kqsx_extract/wp-content/plugins/wp-optimize/cache'
    p2 = '/tmp/kqsx_extract/wp-content/plugins/wp-optimize-premium/cache'
    
    # Also check without leading wp-content in case archive has ./ or site path
    found1 = False
    found2 = False
    for root, dirs, files in os.walk('/tmp/kqsx_extract'):
        if 'wp-optimize' in root and 'cache' in dirs:
            found1 = True
        if 'wp-optimize-premium' in root and 'cache' in dirs:
            found2 = True
            
    if found1 and found2:
        print("SUCCESS! Both cache directories extracted!")
        break

tar_proc.stdin.close()
tar_proc.wait(timeout=10)

print("\nScan results in /tmp/kqsx_extract:")
subprocess.run(['find', '/tmp/kqsx_extract', '-name', '*cache*'])


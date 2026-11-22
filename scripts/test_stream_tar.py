import sys
sys.path.append('/www/server/panel/plugin/gdrive')
from googleapiclient.discovery import build
import gdrive_main
import subprocess

c = gdrive_main.gdrive_main()
c.set_creds()
service = build('drive', 'v3', credentials=c._gdrive_main__creds)

file_id = '1aDJFT5Q0jJcZKyTRi6SIDGxGyKO8UO-j' # web_kqsxmientrung.com_20261031_003951_A0bIHr.tar.gz

req = service.files().get_media(fileId=file_id)

# Pipe stream into tar -tzf - | head -n 30
p = subprocess.Popen(['tar', '-tzf', '-'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

import io
downloader = None
# Just read first 2MB to see archive structure
chunk = req.execute() # Wait, get_media execute() downloads whole file if not using MediaIoBaseDownload
print("Using stream...")


import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = '''
import os, sys, json, time, subprocess, shutil
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError
sys.path.append('/www/server/panel/plugin/gdrive')
import gdrive_main

download_dir = "/www/backup/gdrive_20261026_downloads"
os.makedirs(download_dir, exist_ok=True)
mysql_root_pass = "dc2fe6f2608cdc00"

with open('/tmp/restore_20261026_results.json', 'r') as f:
    prev_results = json.load(f)

with open('/tmp/sites_20261026_inventory.json', 'r') as f:
    inventory = {item["domain"]: item for item in json.load(f)}

# Find failed sites
failed_sites = [r["domain"] for r in prev_results if "DOWNLOAD_ERROR" in r["status"] or "DOWNLOAD_FAILED" in r["status"]]
print(f"Remaining sites to download & restore ({len(failed_sites)}):", failed_sites)

c = gdrive_main.gdrive_main()
c.set_creds()
service = build('drive', 'v3', credentials=c._gdrive_main__creds)

def download_with_retry(filename, target_path, max_retries=3):
    file_id = None
    # 1. Get file id with retry
    for attempt in range(max_retries):
        try:
            results = service.files().list(pageSize=10, q=f"name='{filename}'", fields="files(id, name)").execute()
            items = results.get('files', [])
            if items:
                file_id = items[0]["id"]
                break
        except HttpError as e:
            print(f"    [List Retry {attempt+1}] Rate limit hit, sleeping 15s...")
            time.sleep(15)

    if not file_id:
        raise Exception(f"Could not find file_id for {filename}")

    # 2. Download with 5MB chunks and backoff
    request = service.files().get_media(fileId=file_id)
    tmp_path = f"/tmp/{filename}"
    with open(tmp_path, 'wb') as fh:
        downloader = MediaIoBaseDownload(fh, request, chunksize=5*1024*1024)
        done = False
        while not done:
            for attempt in range(max_retries):
                try:
                    status, done = downloader.next_chunk()
                    if status:
                        print(f"    Progress: {int(status.progress() * 100)}%")
                    time.sleep(1)  # avoid requests per minute quota
                    break
                except HttpError as e:
                    print(f"    [Chunk Retry {attempt+1}] Rate limit hit, sleeping 20s...")
                    time.sleep(20)
            else:
                raise Exception("Failed after max retries")

    shutil.move(tmp_path, target_path)

pass2_results = []
for domain in failed_sites:
    item = inventory[domain]
    db = item["db"]
    backup_info = item["backup"]
    filename = backup_info[1]
    dest_path = os.path.join(download_dir, filename)

    print(f"\\n--- Processing {domain} ({db}) ---")
    print(f"  Filename: {filename}")

    # Check if download needed
    try:
        if not os.path.exists(dest_path) or os.path.getsize(dest_path) < backup_info[4] * 0.95:
            print("  Downloading with rate-limit protection...")
            download_with_retry(filename, dest_path)
            print(f"  Downloaded: {dest_path} ({os.path.getsize(dest_path)} bytes)")
        else:
            print(f"  Already downloaded: {dest_path}")

        # Restore
        print(f"  Restoring into MySQL database {db}...")
        t0 = time.time()
        restore_cmd = f"gunzip -c {dest_path} | mysql -u root -p{mysql_root_pass} {db}"
        p = subprocess.run(restore_cmd, shell=True, capture_output=True, text=True)
        if p.returncode == 0:
            print(f"  RESTORE OK in {time.time()-t0:.1f}s!")
            pass2_results.append({"domain": domain, "db": db, "status": "RESTORED_OK"})
        else:
            print(f"  RESTORE FAILED: {p.stderr}")
            pass2_results.append({"domain": domain, "db": db, "status": f"RESTORE_FAILED: {p.stderr}"})
    except Exception as e:
        print(f"  ERROR for {domain}: {e}")
        pass2_results.append({"domain": domain, "db": db, "status": f"ERROR: {e}"})

    time.sleep(2)  # Pause between sites

# Update global results
updated_results = []
for r in prev_results:
    matched = [p for p in pass2_results if p["domain"] == r["domain"]]
    if matched:
        updated_results.append(matched[0])
    else:
        updated_results.append(r)

with open('/tmp/restore_20261026_results.json', 'w') as f:
    json.dump(updated_results, f, indent=2)

print("\\n=== FINAL SUMMARY OF ALL SITES ===")
for r in updated_results:
    print(f"  {r['domain']} ({r['db']}): {r['status']}")
'''

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
sftp = ssh.open_sftp()
with sftp.file('/tmp/restore_pass2.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('/www/server/panel/pyenv/bin/python3 /tmp/restore_pass2.py')
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
print('STDERR:\n', stderr.read().decode('utf-8', errors='ignore'))
ssh.close()


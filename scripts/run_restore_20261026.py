import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = '''
import os, sys, json, time, subprocess, gzip, shutil

# Load inventory
with open('/tmp/sites_20261026_inventory.json', 'r') as f:
    inventory = json.load(f)

# Rule 0: Backup all current databases first!
backup_dir = "/www/backup/pbn_backups_before_restore_20261026"
os.makedirs(backup_dir, exist_ok=True)
download_dir = "/www/backup/gdrive_20261026_downloads"
os.makedirs(download_dir, exist_ok=True)

print("=== STEP 1: RULE 0 - DUMPING CURRENT DATABASES ===")
mysql_root_pass = "dc2fe6f2608cdc00"

for item in inventory:
    if not item["has_20261026"]:
        continue
    db = item["db"]
    domain = item["domain"]
    cur_dump = os.path.join(backup_dir, f"{domain}_{db}_current.sql.gz")
    if not os.path.exists(cur_dump):
        cmd = f"mysqldump -u root -p{mysql_root_pass} {db} | gzip > {cur_dump}"
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if p.returncode == 0:
            print(f"  [BACKUP OK] {domain} ({db}) -> {cur_dump} ({os.path.getsize(cur_dump)} bytes)")
        else:
            print(f"  [BACKUP FAILED] {domain} ({db}): {p.stderr}")
    else:
        print(f"  [BACKUP EXISTS] {cur_dump}")

# Step 2: Download & Restore from Google Drive
print("\\n=== STEP 2: DOWNLOADING & RESTORING FROM GOOGLE DRIVE ===")
sys.path.append('/www/server/panel/plugin/gdrive')
import gdrive_main

c = gdrive_main.gdrive_main()
c.set_creds()

restore_results = []

for item in inventory:
    domain = item["domain"]
    db = item["db"]
    if not item["has_20261026"]:
        print(f"\\nSkipping {domain}: No 2026-10-26 backup.")
        restore_results.append({"domain": domain, "db": db, "status": "SKIPPED_NO_BACKUP"})
        continue

    backup_info = item["backup"]
    filename = backup_info[1]  # db_wp_...sql.gz
    file_size_expected = backup_info[4]
    dest_path = os.path.join(download_dir, filename)

    print(f"\\nProcessing {domain} (DB: {db}):")
    print(f"  Target backup file: {filename} (~{file_size_expected} bytes)")

    # 2.1 Download file if not yet downloaded or incomplete
    if not os.path.exists(dest_path) or os.path.getsize(dest_path) < file_size_expected * 0.95:
        print(f"  Downloading {filename} from Google Drive...")
        t0 = time.time()
        try:
            # gdrive_main downloads to /tmp/filename
            c.download_file(filename)
            tmp_download = f"/tmp/{filename}"
            if os.path.exists(tmp_download):
                shutil.move(tmp_download, dest_path)
                print(f"  Downloaded in {time.time()-t0:.1f}s -> {dest_path} ({os.path.getsize(dest_path)} bytes)")
            else:
                print(f"  ERROR: Download finished but file not at {tmp_download}")
                restore_results.append({"domain": domain, "db": db, "status": "DOWNLOAD_FAILED"})
                continue
        except Exception as e:
            print(f"  ERROR downloading {filename}: {e}")
            restore_results.append({"domain": domain, "db": db, "status": f"DOWNLOAD_ERROR: {e}"})
            continue
    else:
        print(f"  Already downloaded: {dest_path} ({os.path.getsize(dest_path)} bytes)")

    # 2.2 Restore SQL into Database
    print(f"  Restoring into MySQL database {db}...")
    t0 = time.time()
    restore_cmd = f"gunzip -c {dest_path} | mysql -u root -p{mysql_root_pass} {db}"
    p = subprocess.run(restore_cmd, shell=True, capture_output=True, text=True)
    if p.returncode == 0:
        print(f"  Restore OK in {time.time()-t0:.1f}s!")
        restore_results.append({"domain": domain, "db": db, "status": "RESTORED_OK"})
    else:
        print(f"  Restore FAILED: {p.stderr}")
        restore_results.append({"domain": domain, "db": db, "status": f"RESTORE_FAILED: {p.stderr}"})

# Save results
with open('/tmp/restore_20261026_results.json', 'w') as f:
    json.dump(restore_results, f, indent=2)

print("\\n=== SUMMARY OF RESTORE ===")
for r in restore_results:
    print(f"  {r['domain']} ({r['db']}): {r['status']}")
'''

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
sftp = ssh.open_sftp()
with sftp.file('/tmp/restore_20261026.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('/www/server/panel/pyenv/bin/python3 /tmp/restore_20261026.py')
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
print('STDERR:\n', stderr.read().decode('utf-8', errors='ignore'))
ssh.close()


import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import json, subprocess, datetime, os

with open('/tmp/site_configs.json', 'r') as f:
    configs = json.load(f)

backup_dir = "/www/backup/pbn_backups_before_change"
os.makedirs(backup_dir, exist_ok=True)
timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

print(f"=== STEP 0: BACKING UP ALL 24 DATABASES ({timestamp}) ===")

results = []
for idx, c in enumerate(configs, 1):
    domain = c['domain']
    db = c['db_name']
    out_file = f"{backup_dir}/{domain}_{db}_{timestamp}.sql.gz"
    
    cmd = f"mysqldump -u root -pdc2fe6f2608cdc00 {db} | gzip > {out_file}"
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    size = os.path.getsize(out_file) if os.path.exists(out_file) else 0
    print(f"[{idx:2d}/24] {domain:25s} | db={db:18s} | size={size/1024:8.1f} KB | file={os.path.basename(out_file)}")
    results.append({'idx': idx, 'domain': domain, 'db': db, 'file': out_file, 'size': size})

print("=== BACKUP COMPLETED FOR ALL 24 SITES ===")
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
sftp = ssh.open_sftp()
with sftp.file('/tmp/backup_all_before_change.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/backup_all_before_change.py')
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
print('STDERR:\n', stderr.read().decode('utf-8', errors='ignore'))
ssh.close()


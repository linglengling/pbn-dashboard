import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=15)

backup_cmd = """
mkdir -p /www/backup/pbn_backups_before_backlinks_20261031_step1
cd /www/backup/pbn_backups_before_backlinks_20261031_step1
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

cat /tmp/site_configs.json | python3 -c '
import json, subprocess, sys

with open("/tmp/site_configs.json") as f:
    configs = json.load(f)

for c in configs:
    dom = c["domain"]
    db = c["db_name"]
    out_file = f"/www/backup/pbn_backups_before_backlinks_20261031_step1/{dom}_{db}.sql.gz"
    print(f"Backing up {dom} ({db})...")
    cmd = f"mysqldump -u root -pdc2fe6f2608cdc00 {db} | gzip > {out_file}"
    res = subprocess.run(cmd, shell=True)
    if res.returncode != 0:
        print(f"ERROR backing up {dom}")
        sys.exit(1)
print("All 24 databases backed up successfully!")
'
ls -lh /www/backup/pbn_backups_before_backlinks_20261031_step1
"""

stdin, stdout, stderr = ssh.exec_command(backup_cmd, get_pty=True)
output = stdout.read().decode('utf-8', errors='ignore')
print(output)
ssh.close()


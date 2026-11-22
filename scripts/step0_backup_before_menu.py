import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=15)

backup_cmd = """
mkdir -p /www/backup/pbn_backups_before_menu_20261031_1200
cd /www/backup/pbn_backups_before_menu_20261031_1200

cat /tmp/site_configs.json | python3 -c '
import json, subprocess, sys

with open("/tmp/site_configs.json") as f:
    configs = json.load(f)

for idx, c in enumerate(configs, 1):
    dom = c["domain"]
    db = c["db_name"]
    out_file = f"/www/backup/pbn_backups_before_menu_20261031_1200/{dom}_{db}.sql.gz"
    print(f"[{idx:02d}/24] Backing up {dom} ({db})...")
    cmd = f"mysqldump -u root -pdc2fe6f2608cdc00 {db} | gzip > {out_file}"
    res = subprocess.run(cmd, shell=True)
    if res.returncode != 0:
        print(f"ERROR backing up {dom}")
        sys.exit(1)
print("All 24 databases backed up successfully before menu injection!")
'
ls -lh /www/backup/pbn_backups_before_menu_20261031_1200
"""

stdin, stdout, stderr = ssh.exec_command(backup_cmd, get_pty=True)
for line in iter(stdout.readline, ""):
    print(line, end="")

ssh.close()


import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=15)

remote_code = """
import json, re

with open('/tmp/site_configs.json', 'r') as f:
    configs = json.load(f)

for idx, c in enumerate(configs, 1):
    domain = c['domain']
    pid = c['page_on_front']
    bk_file = f"/tmp/pbn_backups/{domain}_{pid}.sql"
    try:
        with open(bk_file, 'r', errors='ignore') as f:
            content = f.read()
        has_partner = 'partner-network-section' in content
        has_brands = 'Brands' in content
        print(f"{idx:2d}. {domain:25s} | len={len(content):6d} | has_partner={has_partner} | has_brands={has_brands}")
    except Exception as e:
        print(f"{idx:2d}. {domain:25s} | ERR: {e}")
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/inspect_all_pbn_backups.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/inspect_all_pbn_backups.py')
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
print('STDERR:\n', stderr.read().decode('utf-8', errors='ignore'))
ssh.close()


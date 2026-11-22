import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import json, re

with open('/tmp/site_configs.json', 'r') as f:
    configs = json.load(f)

for idx, c in enumerate(configs, 1):
    domain = c['domain']
    pid = c['page_on_front']
    bk_file = f"/tmp/pbn_backups/{domain}_{pid}.sql"
    
    with open(bk_file, 'r', errors='ignore') as f:
        sql = f.read()
    
    # We can extract the values tuple from INSERT INTO `...posts` VALUES (...)
    # Regex to capture the values part
    m = re.search(r'INSERT INTO `[^`]+` VALUES \((.*)\);', sql, flags=re.S)
    if m:
        vals = m.group(1)
        # In MySQL dump of posts table:
        # columns: ID, post_author, post_date, post_date_gmt, post_content, ...
        # Let's verify we can find post_content safely
        print(f"[{idx:2d}/24] {domain:25s} | pid={pid:5d} | values_len={len(vals):6d}")
    else:
        print(f"[{idx:2d}/24] {domain:25s} | ERR: NO INSERT INTO")
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
sftp = ssh.open_sftp()
with sftp.file('/tmp/test_parse_all_bk.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/test_parse_all_bk.py')
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
print('STDERR:\n', stderr.read().decode('utf-8', errors='ignore'))
ssh.close()


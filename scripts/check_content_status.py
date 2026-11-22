import paramiko
import json
import sys

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import json, pymysql

with open('/tmp/site_configs.json', 'r') as f:
    configs = json.load(f)

for idx, c in enumerate(configs, 1):
    db = c['db_name']
    prefix = c['prefix']
    domain = c['domain']
    pid = c['page_on_front']
    
    conn = pymysql.connect(host='127.0.0.1', user='root', password='dc2fe6f2608cdc00', database=db)
    cur = conn.cursor()
    cur.execute(f"SELECT post_content FROM {prefix}posts WHERE ID=%s", (pid,))
    row = cur.fetchone()
    content = row[0] if row else ""
    
    has_network_section = 'partner-network-section' in content or 'recommended-gaming-section' in content
    has_casino_5 = any(k in content for k in ['ivibet', 'b2xbet', 'megapari', 'freshcasino', 'jetcasino'])
    has_slash_n = '\\\\n' in content
    
    print(f"{idx:2d}. {domain:25s} | len={len(content):6d} | network_sec={has_network_section} | 5_brands={has_casino_5} | slash_n={has_slash_n}")
    conn.close()
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_content_status.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/check_content_status.py')
sys.stdout.reconfigure(encoding='utf-8')
print("STDOUT:\n", stdout.read().decode('utf-8', errors='ignore'))
ssh.close()


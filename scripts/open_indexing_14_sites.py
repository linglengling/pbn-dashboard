import paramiko
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('indexing_audit_result.json', 'r', encoding='utf-8') as f:
    audit = json.load(f)

sites_to_open = [s for s in audit if not s['is_index_open']]

print(f"Opening index for {len(sites_to_open)} sites...")
for s in sites_to_open:
    print(f"- #{s['idx']:2d} {s['domain']} (DB: {s['db_name']}, Prefix: {s['prefix']})")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=15)

remote_script = """
import json
import pymysql
import os
import urllib.request
import ssl
import re
import time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

with open('/tmp/sites_to_open.json', 'r') as f:
    sites = json.load(f)

db = pymysql.connect(host='127.0.0.1', user='root', password='dc2fe6f2608cdc00')
cursor = db.cursor()

print("1. Updating blog_public = '1' in database...")
for s in sites:
    db_name = s['db_name']
    prefix = s['prefix']
    domain = s['domain']
    
    # Check if blog_public exists
    cursor.execute(f"SELECT option_value FROM `{db_name}`.`{prefix}options` WHERE option_name = 'blog_public'")
    row = cursor.fetchone()
    if row is not None:
        cursor.execute(f"UPDATE `{db_name}`.`{prefix}options` SET option_value = '1' WHERE option_name = 'blog_public'")
    else:
        cursor.execute(f"INSERT INTO `{db_name}`.`{prefix}options` (option_name, option_value, autoload) VALUES ('blog_public', '1', 'yes')")
    db.commit()
    print(f"  [OK] Updated {domain} ({db_name}) -> blog_public = 1")

db.close()

# 2. Clear OpenLiteSpeed cache and restart lsws
print("\\n2. Clearing web server cache & restarting LiteSpeed...")
os.system("rm -rf /usr/local/lsws/cachedata/priv/*")
os.system("/usr/local/lsws/bin/lswsctrl restart")
time.sleep(3)

# 3. Verify live HTML on all 14 sites
print("\\n3. Verifying live HTML for index status...")
results = []
for s in sites:
    domain = s['domain']
    live_meta = "none"
    http_status = 0
    try:
        req = urllib.request.Request(f"https://{domain}/?nocache={int(time.time())}", headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            http_status = resp.status
            html = resp.read().decode('utf-8', errors='ignore')
            m = re.search(r'<meta[^>]+name=["\\']robots["\\'][^>]+content=["\\']([^"\\']+)["\\']', html, re.I)
            if not m:
                m = re.search(r'<meta[^>]+content=["\\']([^"\\']+)["\\'][^>]+name=["\\']robots["\\']', html, re.I)
            if m:
                live_meta = m.group(1)
    except Exception as e:
        live_meta = f"ERR: {str(e)[:30]}"
    
    has_noindex = 'noindex' in live_meta.lower()
    results.append({
        'idx': s['idx'],
        'domain': domain,
        'http_status': http_status,
        'live_meta': live_meta,
        'is_open': not has_noindex
    })
    print(f"  #{s['idx']:2d} | {domain:25s} | HTTP {http_status} | Meta: {live_meta} | Status: {'OPEN (INDEXED)' if not has_noindex else 'STILL NOINDEX'}")

print(json.dumps(results))
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/sites_to_open.json', 'w') as f:
    json.dump(sites_to_open, f)

with sftp.file('/tmp/remote_open_indexing.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('/www/server/panel/pyenv/bin/python3 /tmp/remote_open_indexing.py')
out = stdout.read().decode()
err = stderr.read().decode()

print("\n=== EXECUTION OUTPUT ===")
print(out)
if err:
    print("=== STDERR ===")
    print(err)

ssh.close()


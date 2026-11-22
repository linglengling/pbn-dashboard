import paramiko
import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

target_sites = [
    "aaidudec.org", "anthonyruivivar.net", "bblatinamerica.com", "conadecivil.com",
    "facturatabasco.com", "greatdrivingchallenge.com", "hkhoe.com", "sburlrecdept.com",
    "shadowdance.org", "smvhighschool.in", "snow-design.com", "stepl.org",
    "suzanneloebl.com", "thaiasiatoday.com", "feshun.com", "hellbenderpress.com",
    "innkeeperrockies.com", "rogalevich.org", "j-core.biz", "kvdevelopers.com",
    "benscarpage.com", "kylehendersonmusic.com", "respectablyfrench.com", "sougicocoro.com"
]

remote_code = f'''
import sqlite3, os, json

target_sites = {json.dumps(target_sites)}

# 1. Read wp-config for each site to get exact db_name
site_dbs = {{}}
for domain in target_sites:
    wp_config = f"/www/wwwroot/{{domain}}/wp-config.php"
    if os.path.exists(wp_config):
        with open(wp_config, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            db_name = None
            for line in content.splitlines():
                if 'DB_NAME' in line:
                    parts = line.split(',')
                    if len(parts) > 1:
                        db_name = parts[1].split(')')[0].strip().strip("'").strip('"')
            site_dbs[domain] = db_name
    else:
        site_dbs[domain] = None

print("Domain -> DB mapping:")
for d, db in site_dbs.items():
    print(f"  {{d}}: {{db}}")

# 2. Check backup table in aaPanel default.db for 2026-10-26
conn = sqlite3.connect('/www/server/panel/data/default.db')
cur = conn.cursor()

results = []
for domain in target_sites:
    db = site_dbs.get(domain)
    if not db:
        results.append({{"domain": domain, "db": None, "has_20261026": False, "backup": None}})
        continue
    
    # Query backups for this db around 2026-10-26
    cur.execute("SELECT id, name, filename, addtime, size FROM backup WHERE type=1 AND name LIKE ? AND addtime LIKE '2026-10-26%'", (f"%{{db}}%",))
    rows = cur.fetchall()
    if rows:
        results.append({{"domain": domain, "db": db, "has_20261026": True, "backup": rows[0]}})
    else:
        results.append({{"domain": domain, "db": db, "has_20261026": False, "backup": None}})

conn.close()

print("\\n--- BACKUP 2026-10-26 STATUS ---")
count_has = 0
for r in results:
    if r["has_20261026"]:
        b = r["backup"]
        print(f"[FOUND] {{r['domain']}} (DB: {{r['db']}}) -> {{b[1]}} | {{b[3]}} | {{b[4]}} bytes")
        count_has += 1
    else:
        print(f"[NOT FOUND] {{r['domain']}} (DB: {{r['db']}})")

print(f"\\nTotal sites with 2026-10-26 backup: {{count_has}} / {{len(target_sites)}}")
with open('/tmp/sites_20261026_inventory.json', 'w') as f:
    json.dump(results, f, indent=2)
'''

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
sftp = ssh.open_sftp()
with sftp.file('/tmp/check_sites_20261026.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/check_sites_20261026.py')
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
print('STDERR:\n', stderr.read().decode('utf-8', errors='ignore'))
ssh.close()


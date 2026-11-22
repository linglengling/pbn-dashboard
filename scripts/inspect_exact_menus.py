import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=15)

remote_py = """import json, pymysql, re

with open("/tmp/site_configs.json") as f:
    configs = json.load(f)

for idx, c in enumerate(configs, 1):
    dom = c["domain"]
    db = c["db_name"]
    pfx = c["prefix"]
    
    conn = pymysql.connect(host="127.0.0.1", user="root", password="dc2fe6f2608cdc00", database=db)
    cur = conn.cursor()
    
    # 1. Get stylesheet
    cur.execute(f"SELECT option_value FROM {pfx}options WHERE option_name='stylesheet'")
    r_sheet = cur.fetchone()
    stylesheet = r_sheet[0] if r_sheet else ""
    
    # 2. Get theme_mods
    cur.execute(f"SELECT option_value FROM {pfx}options WHERE option_name=%s", (f"theme_mods_{stylesheet}",))
    r_mods = cur.fetchone()
    mods_raw = r_mods[0] if r_mods else ""
    
    # Extract nav_menu_locations
    m = re.search(r'nav_menu_locations\";a:\d+:\{(.*?)\}', mods_raw)
    loc_info = m.group(1) if m else "NONE"
    
    # 3. Get all nav_menu terms
    cur.execute(f"SELECT t.term_id, t.name, tt.count FROM {pfx}terms t JOIN {pfx}term_taxonomy tt ON t.term_id=tt.term_id WHERE tt.taxonomy='nav_menu'")
    menus = cur.fetchall()
    
    print(f"[{idx:02d}] {dom:26s} | theme={stylesheet:15s} | locs={loc_info} | menus={menus}")
    conn.close()
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/inspect_exact_menus.py', 'w') as f:
    f.write(remote_py)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/inspect_exact_menus.py')
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
print('STDERR:\n', stderr.read().decode('utf-8', errors='ignore'))
ssh.close()

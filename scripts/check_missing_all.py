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

for c in configs:
    db = c['db_name']
    prefix = c['prefix']
    domain = c['domain']
    
    conn = pymysql.connect(host='127.0.0.1', user='root', password='dc2fe6f2608cdc00', database=db)
    cur = conn.cursor()
    
    # Check page templates in postmeta
    cur.execute(f"SELECT DISTINCT post_id FROM {prefix}postmeta WHERE meta_key='_wp_page_template'")
    page_ids = [r[0] for r in cur.fetchall()]
    
    # Check menu items in postmeta
    cur.execute(f"SELECT DISTINCT post_id FROM {prefix}postmeta WHERE meta_key='_menu_item_object_id'")
    menu_item_ids = [r[0] for r in cur.fetchall()]
    
    # Check target objects of menu items
    cur.execute(f"SELECT meta_value FROM {prefix}postmeta WHERE meta_key='_menu_item_object_id' AND meta_value != '0' AND meta_value != ''")
    target_ids = set(r[0] for r in cur.fetchall())
    
    # Check existing posts in posts table
    cur.execute(f"SELECT ID FROM {prefix}posts")
    existing_posts = set(r[0] for r in cur.fetchall())
    
    missing_pages = [pid for pid in page_ids if pid not in existing_posts]
    missing_menu_items = [mid for mid in menu_item_ids if mid not in existing_posts]
    
    print(f"{domain:25s} | Pages: {len(page_ids):2d} (missing: {len(missing_pages):2d}) | MenuItems: {len(menu_item_ids):2d} (missing: {len(missing_menu_items):2d})")
    conn.close()
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_missing_all.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/check_missing_all.py')
sys.stdout.reconfigure(encoding='utf-8')
print("STDOUT:\n", stdout.read().decode('utf-8', errors='ignore'))
ssh.close()


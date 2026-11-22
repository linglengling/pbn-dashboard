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
    
    conn = pymysql.connect(host='127.0.0.1', user='root', password='dc2fe6f2608cdc00', database=db)
    cur = conn.cursor()
    
    # Check if 'Brands' exists in posts as nav_menu_item
    cur.execute(f"SELECT ID, post_title FROM {prefix}posts WHERE post_type='nav_menu_item' AND post_title='Brands'")
    brands = cur.fetchall()
    
    # Check total nav_menu_items
    cur.execute(f"SELECT count(*) FROM {prefix}posts WHERE post_type='nav_menu_item'")
    total_nav = cur.fetchone()[0]
    
    expected_brand = 'BU88 / VB88' if idx % 2 != 0 else 'X8 Club / HD88'
    print(f"{idx:2d}. {domain:25s} | total_nav={total_nav:2d} | has_Brands={len(brands) > 0} | expected={expected_brand}")
    conn.close()
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_all_menus.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/check_all_menus.py')
sys.stdout.reconfigure(encoding='utf-8')
print("STDOUT:\n", stdout.read().decode('utf-8', errors='ignore'))
ssh.close()


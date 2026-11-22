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
    pid = c['page_on_front']
    
    conn = pymysql.connect(host='127.0.0.1', user='root', password='dc2fe6f2608cdc00', database=db)
    cur = conn.cursor()
    
    # Check total posts
    cur.execute(f"SELECT count(*) FROM {prefix}posts")
    posts_cnt = cur.fetchone()[0]
    
    # Check postmeta unique post_ids
    cur.execute(f"SELECT count(DISTINCT post_id) FROM {prefix}postmeta")
    pm_cnt = cur.fetchone()[0]
    
    # Check how many nav_menu_items in postmeta
    cur.execute(f"SELECT count(DISTINCT post_id) FROM {prefix}postmeta WHERE meta_key='_menu_item_object_id'")
    menu_pm_cnt = cur.fetchone()[0]
    
    # Check how many pages in postmeta
    cur.execute(f"SELECT count(DISTINCT post_id) FROM {prefix}postmeta WHERE meta_key='_wp_page_template'")
    page_pm_cnt = cur.fetchone()[0]
    
    # Check term_relationships count
    cur.execute(f"SELECT count(*) FROM {prefix}term_relationships")
    tr_cnt = cur.fetchone()[0]
    
    print(f"{domain:25s} | posts:{posts_cnt:3d} | postmeta_ids:{pm_cnt:4d} | menu_ids:{menu_pm_cnt:3d} | page_ids:{page_pm_cnt:3d} | tr:{tr_cnt:4d}")
    conn.close()
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)

sftp = ssh.open_sftp()
with sftp.file('/tmp/inspect_all_meta.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/inspect_all_meta.py')
sys.stdout.reconfigure(encoding='utf-8')
print("STDOUT:\n", stdout.read().decode('utf-8', errors='ignore'))
print("STDERR:\n", stderr.read().decode('utf-8', errors='ignore'))
ssh.close()


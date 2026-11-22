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

the_7_dbs = {
    'wp_j-core_biz', 'wp_kvdevelopers', 'wp_rogalevich_or',
    'wp_sburlrecdept', 'wp_shadowdance_o', 'wp_smvhighschool', 'wp_snow-design_c'
}

for c in configs:
    db = c['db_name']
    if db in the_7_dbs:
        continue
    prefix = c['prefix']
    domain = c['domain']
    
    conn = pymysql.connect(host='127.0.0.1', user='root', password='dc2fe6f2608cdc00', database=db)
    cur = conn.cursor()
    
    # Check post_ids in postmeta grouped by type indicators
    cur.execute(f"SELECT DISTINCT post_id FROM {prefix}postmeta WHERE meta_key='_wp_attached_file'")
    attachments = set(r[0] for r in cur.fetchall())
    
    cur.execute(f"SELECT DISTINCT post_id FROM {prefix}postmeta WHERE meta_key='_wp_page_template'")
    pages = set(r[0] for r in cur.fetchall())
    
    cur.execute(f"SELECT DISTINCT post_id FROM {prefix}postmeta WHERE meta_key='_menu_item_object_id'")
    menu_items = set(r[0] for r in cur.fetchall())
    
    cur.execute(f"SELECT DISTINCT post_id FROM {prefix}postmeta WHERE meta_key='_generate_element_type'")
    gp_elements = set(r[0] for r in cur.fetchall())
    
    cur.execute(f"SELECT DISTINCT post_id FROM {prefix}postmeta")
    all_pm_posts = set(r[0] for r in cur.fetchall())
    
    accounted = attachments | pages | menu_items | gp_elements
    other_posts = all_pm_posts - accounted
    
    print(f"{domain:25s} | total_pm={len(all_pm_posts):4d} | pages={len(pages):2d} | menus={len(menu_items):2d} | attach={len(attachments):3d} | gp={len(gp_elements):2d} | other={len(other_posts):3d}")
    conn.close()
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_other_17_types.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/check_other_17_types.py')
sys.stdout.reconfigure(encoding='utf-8')
print("STDOUT:\n", stdout.read().decode('utf-8', errors='ignore'))
ssh.close()


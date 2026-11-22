import paramiko
import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import json, pymysql, subprocess

with open('/tmp/site_configs.json', 'r') as f:
    configs = json.load(f)

print("=== REMOVING BRAND NAV ITEMS FROM ALL 24 SITES ===")

for idx, c in enumerate(configs, 1):
    db = c['db_name']
    prefix = c['prefix']
    domain = c['domain']
    
    conn = pymysql.connect(host='127.0.0.1', user='root', password='dc2fe6f2608cdc00', database=db)
    cur = conn.cursor()
    
    # Find brand nav menu items
    cur.execute(f'''
        SELECT ID, post_title FROM {prefix}posts 
        WHERE post_type='nav_menu_item' 
        AND (post_title IN ('Brands', 'BU88', 'VB88', 'X8 Club', 'HD88')
             OR post_name IN ('brands', 'bu88', 'vb88', 'x8-club', 'hd88'))
    ''')
    rows = cur.fetchall()
    
    if rows:
        ids = [r[0] for r in rows]
        id_placeholders = ','.join(['%s'] * len(ids))
        
        # 1. Delete from postmeta
        cur.execute(f"DELETE FROM {prefix}postmeta WHERE post_id IN ({id_placeholders})", ids)
        meta_deleted = cur.rowcount
        
        # 2. Delete from term_relationships
        cur.execute(f"DELETE FROM {prefix}term_relationships WHERE object_id IN ({id_placeholders})", ids)
        term_rel_deleted = cur.rowcount
        
        # 3. Delete from posts
        cur.execute(f"DELETE FROM {prefix}posts WHERE ID IN ({id_placeholders})", ids)
        posts_deleted = cur.rowcount
        
        # 4. Recalculate nav_menu term counts
        cur.execute(f'''
            UPDATE {prefix}term_taxonomy tt
            SET count = (
                SELECT count(*) FROM {prefix}term_relationships tr
                WHERE tr.term_taxonomy_id = tt.term_taxonomy_id
            )
            WHERE tt.taxonomy = 'nav_menu'
        ''')
        
        conn.commit()
        print(f"[{idx:2d}/24] {domain:25s}: Deleted {posts_deleted} nav items (IDs: {ids}), {meta_deleted} meta, {term_rel_deleted} rels.")
    else:
        print(f"[{idx:2d}/24] {domain:25s}: No brand nav items found.")
        
    conn.close()

# Flush caches
print("\\n=== FLUSHING ALL CACHES ===")
subprocess.run("rm -rf /www/wwwroot/*/wp-content/cache/*", shell=True)
subprocess.run("rm -rf /www/server/lscache/* /tmp/lscache/*", shell=True)
print("Cache directories cleared.")
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
sftp = ssh.open_sftp()
with sftp.file('/tmp/remove_brand_menus.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/remove_brand_menus.py')
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
print('STDERR:\n', stderr.read().decode('utf-8', errors='ignore'))
ssh.close()


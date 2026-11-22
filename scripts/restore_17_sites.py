import paramiko
import json
import sys

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import json, pymysql, re, subprocess

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
    
    # 1. Get existing posts
    cur.execute(f"SELECT ID FROM {prefix}posts")
    existing_ids = set(r[0] for r in cur.fetchall())
    
    # 2. Get all distinct post_ids in postmeta
    cur.execute(f"SELECT DISTINCT post_id FROM {prefix}postmeta")
    all_pm_ids = [r[0] for r in cur.fetchall()]
    
    inserted_cnt = 0
    for pid in all_pm_ids:
        if pid in existing_ids:
            continue
            
        cur.execute(f"SELECT meta_key, meta_value FROM {prefix}postmeta WHERE post_id=%s", (pid,))
        meta = dict(cur.fetchall())
        
        post_type = 'post'
        post_title = ''
        post_name = str(pid)
        post_status = 'publish'
        post_mime_type = ''
        
        if '_menu_item_object_id' in meta:
            post_type = 'nav_menu_item'
            post_status = 'publish'
        elif '_wp_attached_file' in meta:
            post_type = 'attachment'
            post_status = 'inherit'
            file_path = meta.get('_wp_attached_file', '')
            post_title = file_path.split('/')[-1] if file_path else f"Attachment {pid}"
            # Extract extension for mime_type
            ext = post_title.split('.')[-1].lower() if '.' in post_title else ''
            if ext in ('jpg', 'jpeg'):
                post_mime_type = 'image/jpeg'
            elif ext == 'png':
                post_mime_type = 'image/png'
            elif ext == 'webp':
                post_mime_type = 'image/webp'
            elif ext == 'svg':
                post_mime_type = 'image/svg+xml'
            elif ext == 'gif':
                post_mime_type = 'image/gif'
        elif '_generate_element_type' in meta:
            post_type = 'gp_elements'
            post_status = 'publish'
            post_title = meta.get('_generate_element_type', 'Element').title()
        elif '_wp_page_template' in meta or meta.get('_menu_item_object') == 'page':
            post_type = 'page'
            post_status = 'publish'
            title = meta.get('rank_math_title', '')
            if title:
                post_title = title.split('|')[0].strip()
                post_title = re.sub(r'&#8211;|–|-|&amp;', '', post_title).strip()
            else:
                post_title = meta.get('rank_math_focus_keyword', f'Page {pid}').title()
            slug = meta.get('rank_math_focus_keyword', str(pid)).lower().replace(' ', '-')
            post_name = re.sub(r'[^a-z0-9\-]', '', slug)
        else:
            # Regular post
            post_type = 'post'
            post_status = 'publish'
            title = meta.get('rank_math_title', '')
            if title:
                post_title = title.split('|')[0].strip()
                post_title = re.sub(r'&#8211;|–|-|&amp;', '', post_title).strip()
            else:
                post_title = meta.get('rank_math_focus_keyword', f'Post {pid}').title()
            slug = meta.get('rank_math_focus_keyword', str(pid)).lower().replace(' ', '-')
            post_name = re.sub(r'[^a-z0-9\-]', '', slug)
            
        cur.execute(f\"\"\"
            INSERT INTO {prefix}posts
            (ID, post_author, post_date, post_date_gmt, post_content, post_title, post_excerpt,
             post_status, comment_status, ping_status, post_name, to_ping, pinged,
             post_modified, post_modified_gmt, post_content_filtered, post_parent, guid,
             menu_order, post_type, post_mime_type, comment_count)
            VALUES (%s, 1, NOW(), NOW(), '', %s, '', %s, 'closed', 'closed', %s, '', '', NOW(), NOW(), '', 0, '', 0, %s, %s, 0)
        \"\"\", (pid, post_title, post_status, post_name, post_type, post_mime_type))
        inserted_cnt += 1
        
    conn.commit()
    cur.execute(f"SELECT count(*) FROM {prefix}posts")
    total = cur.fetchone()[0]
    conn.close()
    print(f"Restored {domain:25s} ({db}): inserted {inserted_cnt:4d} rows, total_posts now={total:4d}")

subprocess.run("rm -rf /usr/local/lsws/cachedata/priv/*", shell=True)
subprocess.run("/usr/local/lsws/bin/lswsctrl reload", shell=True)
print("LSWS cache cleared and reloaded.")
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)

sftp = ssh.open_sftp()
with sftp.file('/tmp/restore_17_sites.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/restore_17_sites.py')
sys.stdout.reconfigure(encoding='utf-8')
print("STDOUT:\n", stdout.read().decode('utf-8', errors='ignore'))
print("STDERR:\n", stderr.read().decode('utf-8', errors='ignore'))
ssh.close()


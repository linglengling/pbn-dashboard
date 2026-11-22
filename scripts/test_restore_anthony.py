import paramiko
import sys

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import pymysql, re, subprocess

conn = pymysql.connect(host='127.0.0.1', user='root', password='dc2fe6f2608cdc00', database='wp_anthonyruiviv')
cur = conn.cursor()

# Get missing pages
cur.execute("SELECT DISTINCT post_id FROM wp_postmeta WHERE meta_key='_wp_page_template'")
page_ids = [r[0] for r in cur.fetchall()]

cur.execute("SELECT ID FROM wp_posts")
existing_ids = set(r[0] for r in cur.fetchall())

inserted_pages = 0
for pid in page_ids:
    if pid not in existing_ids:
        cur.execute("SELECT meta_key, meta_value FROM wp_postmeta WHERE post_id=%s", (pid,))
        meta = dict(cur.fetchall())
        
        # Determine title
        title = meta.get('rank_math_title', '')
        # Clean title (e.g. 'How to Deposit on Jiliasia | Easy, Secure...' -> take before |)
        if title:
            clean_title = title.split('|')[0].strip()
            clean_title = re.sub(r'&#8211;|–|-|&amp;', '', clean_title).strip()
        else:
            clean_title = meta.get('rank_math_focus_keyword', f'Page {pid}').title()
            
        slug = meta.get('rank_math_focus_keyword', str(pid)).lower().replace(' ', '-')
        slug = re.sub(r'[^a-z0-9\-]', '', slug)
        
        cur.execute(\"\"\"
            INSERT INTO wp_posts
            (ID, post_author, post_date, post_date_gmt, post_content, post_title, post_excerpt,
             post_status, comment_status, ping_status, post_name, to_ping, pinged,
             post_modified, post_modified_gmt, post_content_filtered, post_parent, guid,
             menu_order, post_type, post_mime_type, comment_count)
            VALUES (%s, 1, NOW(), NOW(), '', %s, '', 'publish', 'closed', 'closed', %s, '', '', NOW(), NOW(), '', 0, '', 0, 'page', '', 0)
        \"\"\", (pid, clean_title, slug))
        inserted_pages += 1

print(f"Inserted {inserted_pages} missing pages into wp_posts.")

# Also check missing nav_menu_items
cur.execute("SELECT DISTINCT post_id FROM wp_postmeta WHERE meta_key='_menu_item_object_id'")
menu_item_ids = [r[0] for r in cur.fetchall()]
cur.execute("SELECT ID FROM wp_posts")
existing_ids = set(r[0] for r in cur.fetchall())

inserted_menus = 0
for mid in menu_item_ids:
    if mid not in existing_ids:
        cur.execute(\"\"\"
            INSERT INTO wp_posts
            (ID, post_author, post_date, post_date_gmt, post_content, post_title, post_excerpt,
             post_status, comment_status, ping_status, post_name, to_ping, pinged,
             post_modified, post_modified_gmt, post_content_filtered, post_parent, guid,
             menu_order, post_type, post_mime_type, comment_count)
            VALUES (%s, 1, NOW(), NOW(), '', '', '', 'publish', 'closed', 'closed', %s, '', '', NOW(), NOW(), '', 0, '', 0, 'nav_menu_item', '', 0)
        \"\"\", (mid, str(mid)))
        inserted_menus += 1

print(f"Inserted {inserted_menus} missing nav_menu_items.")

conn.commit()
conn.close()

# Clear cache
subprocess.run("rm -rf /usr/local/lsws/cachedata/priv/*", shell=True)
subprocess.run("/usr/local/lsws/bin/lswsctrl reload", shell=True)
print("LSWS cache cleared and reloaded.")
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)

sftp = ssh.open_sftp()
with sftp.file('/tmp/test_restore_anthony.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/test_restore_anthony.py')
sys.stdout.reconfigure(encoding='utf-8')
print("STDOUT:\n", stdout.read().decode('utf-8', errors='ignore'))
print("STDERR:\n", stderr.read().decode('utf-8', errors='ignore'))
ssh.close()


import paramiko

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import pymysql

conn = pymysql.connect(host='127.0.0.1', user='root', password='dc2fe6f2608cdc00', database='wp_aaidudec_org')
cur = conn.cursor()

# Check nav menus (terms with taxonomy nav_menu)
cur.execute('''
SELECT t.term_id, t.name, t.slug, tt.term_taxonomy_id, tt.count
FROM wp_terms t
JOIN wp_term_taxonomy tt ON t.term_id = tt.term_id
WHERE tt.taxonomy = 'nav_menu'
''')
print('NAV MENUS:', cur.fetchall())

# Check menu locations in theme_mods
cur.execute("SELECT option_name, option_value FROM wp_options WHERE option_name LIKE 'theme_mods_%'")
for row in cur.fetchall():
    print('THEME MOD:', row[0], row[1][:300])

# Check all nav_menu_item posts
cur.execute('''
SELECT p.ID, p.post_title, p.post_status, p.post_name, p.menu_order, p.post_parent, tr.term_taxonomy_id
FROM wp_posts p
LEFT JOIN wp_term_relationships tr ON p.ID = tr.object_id
WHERE p.post_type = 'nav_menu_item'
ORDER BY p.ID
''')
for row in cur.fetchall():
    print('NAV ITEM:', row)

# Check postmeta for nav_menu_items
cur.execute('''
SELECT post_id, meta_key, meta_value
FROM wp_postmeta
WHERE post_id IN (SELECT ID FROM wp_posts WHERE post_type = 'nav_menu_item')
ORDER BY post_id, meta_key
''')
postmeta = cur.fetchall()
print(f'Total postmeta rows for nav items: {len(postmeta)}')
for row in postmeta:
    print('  META:', row)

conn.close()
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
sftp = ssh.open_sftp()
with sftp.file('/tmp/inspect_aaidudec_nav.py', 'w') as f:
    f.write(remote_code)
sftp.close()
stdin, stdout, stderr = ssh.exec_command('python3 /tmp/inspect_aaidudec_nav.py')
print(stdout.read().decode('utf-8', errors='ignore'))
ssh.close()


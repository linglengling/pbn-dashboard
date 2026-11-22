import paramiko

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import pymysql, subprocess

conn = pymysql.connect(host='127.0.0.1', user='root', password='dc2fe6f2608cdc00', database='wp_anthonyruiviv')
cur = conn.cursor()

# Find all nav_menu_item post_ids in wp_postmeta
cur.execute("SELECT DISTINCT post_id FROM wp_postmeta WHERE meta_key='_menu_item_object_id'")
menu_item_ids = [r[0] for r in cur.fetchall()]
print("Found menu item IDs:", menu_item_ids)

# Check which ones are already in wp_posts
cur.execute("SELECT ID FROM wp_posts WHERE ID IN (%s)" % ','.join(map(str, menu_item_ids)))
existing_ids = set(r[0] for r in cur.fetchall())

order = 1
for mid in menu_item_ids:
    if mid not in existing_ids:
        cur.execute(\"\"\"
            INSERT INTO wp_posts 
            (ID, post_author, post_date, post_date_gmt, post_content, post_title, post_excerpt, post_status, comment_status, ping_status, post_name, to_ping, pinged, post_modified, post_modified_gmt, post_content_filtered, post_parent, guid, menu_order, post_type, post_mime_type, comment_count)
            VALUES (%s, 1, NOW(), NOW(), '', '', '', 'publish', 'closed', 'closed', %s, '', '', NOW(), NOW(), '', 0, '', %s, 'nav_menu_item', '', 0)
        \"\"\", (mid, str(mid), order))
        order += 1

conn.commit()
conn.close()

# Clear cache and reload
subprocess.run("rm -rf /usr/local/lsws/cachedata/priv/*", shell=True)
subprocess.run("/usr/local/lsws/bin/lswsctrl reload", shell=True)
print("Inserted missing nav_menu_items and reloaded!")
"""

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
    
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/restore_menu_anthony.py', 'w') as f:
        f.write(remote_code)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command('python3 /tmp/restore_menu_anthony.py')
    print(stdout.read().decode('utf-8'))
    ssh.close()

if __name__ == "__main__":
    main()


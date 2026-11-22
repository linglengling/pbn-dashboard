import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import pymysql

conn = pymysql.connect(host='127.0.0.1', user='root', password='dc2fe6f2608cdc00', database='wp_aaidudec_org')
cur = conn.cursor()

# Check target posts: 24, 72, 79, 94, 785
cur.execute('SELECT ID, post_title, post_status, post_type FROM wp_posts WHERE ID IN (24, 72, 79, 94, 785)')
print('TARGET POSTS:', cur.fetchall())

# Check target terms: 1, 2, 3, 4, 5
cur.execute('SELECT term_id, name, slug FROM wp_terms WHERE term_id IN (1, 2, 3, 4, 5)')
print('TARGET TERMS:', cur.fetchall())

# Check term taxonomy
cur.execute('SELECT term_taxonomy_id, term_id, taxonomy, count FROM wp_term_taxonomy WHERE term_id IN (1, 2, 3, 4, 5)')
print('TARGET TERM TAXONOMY:', cur.fetchall())

# Check all non-nav posts in wp_posts
cur.execute("SELECT ID, post_title, post_status, post_type FROM wp_posts WHERE post_type != 'nav_menu_item'")
all_posts = cur.fetchall()
print(f'Total non-nav posts in wp_posts: {len(all_posts)}')
for p in all_posts:
    print('  NON-NAV POST:', p)

conn.close()
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
sftp = ssh.open_sftp()
with sftp.file('/tmp/inspect_target_posts.py', 'w') as f:
    f.write(remote_code)
sftp.close()
stdin, stdout, stderr = ssh.exec_command('python3 /tmp/inspect_target_posts.py')
print(stdout.read().decode('utf-8', errors='ignore'))
ssh.close()

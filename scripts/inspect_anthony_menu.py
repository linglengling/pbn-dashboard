import paramiko
import sys

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import pymysql

conn = pymysql.connect(host='127.0.0.1', user='root', password='dc2fe6f2608cdc00', database='wp_anthonyruiviv')
cur = conn.cursor()

# Get nav menus
cur.execute(\"\"\"
    SELECT t.term_id, t.name, t.slug, tt.term_taxonomy_id, tt.count
    FROM wp_terms t
    JOIN wp_term_taxonomy tt ON t.term_id = tt.term_id
    WHERE tt.taxonomy = 'nav_menu'
\"\"\")
menus = cur.fetchall()
print("Nav Menus in anthonyruivivar:", menus)

# Check theme locations in wp_options
cur.execute("SELECT option_name, option_value FROM wp_options WHERE option_name LIKE 'theme_mods_%' OR option_name = 'nav_menu_options'")
print("Theme mods / menu options:", cur.fetchall())

cur.execute("SELECT post_id, meta_key, meta_value FROM wp_postmeta WHERE post_id IN (65, 69, 68, 701) ORDER BY post_id, meta_key")
for r in cur.fetchall():
    print(r)
conn.close()
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)

sftp = ssh.open_sftp()
with sftp.file('/tmp/inspect_anthony_menu.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/inspect_anthony_menu.py')
sys.stdout.reconfigure(encoding='utf-8')
print("STDOUT:\n", stdout.read().decode('utf-8', errors='ignore'))
print("STDERR:\n", stderr.read().decode('utf-8', errors='ignore'))
ssh.close()

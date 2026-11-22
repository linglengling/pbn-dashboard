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

cur.execute(\"\"\"
    SELECT tr.object_id
    FROM wp_term_relationships tr
    WHERE tr.term_taxonomy_id = 180
\"\"\")
mids = [r[0] for r in cur.fetchall()]

for mid in mids:
    cur.execute("SELECT meta_key, meta_value FROM wp_postmeta WHERE post_id=%s", (mid,))
    meta = dict(cur.fetchall())
    obj_id = meta.get('_menu_item_object_id')
    parent_id = meta.get('_menu_item_menu_item_parent')
    m_type = meta.get('_menu_item_type')
    url = meta.get('_menu_item_url')
    print(f"MenuItem {mid}: parent={parent_id}, type={m_type}, obj_id={obj_id}, url='{url}'")

conn.close()
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_menu_180.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/check_menu_180.py')
sys.stdout.reconfigure(encoding='utf-8')
print("STDOUT:\n", stdout.read().decode('utf-8', errors='ignore'))
ssh.close()


import paramiko
import sys

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import pymysql

conn = pymysql.connect(host='127.0.0.1', user='root', password='dc2fe6f2608cdc00', database='wp_aaidudec_org')
cur = conn.cursor()

# Check what post_ids exist in aaidudec postmeta that are not attachments, menus, gp_elements
cur.execute(\"\"\"
    SELECT post_id, GROUP_CONCAT(meta_key)
    FROM wp_postmeta
    WHERE post_id NOT IN (
        SELECT DISTINCT post_id FROM wp_postmeta WHERE meta_key IN ('_wp_attached_file', '_menu_item_object_id', '_generate_element_type', '_wp_page_template')
    )
    GROUP BY post_id
    LIMIT 20
\"\"\")
for r in cur.fetchall():
    print(f"ID {r[0]}: {r[1][:100]}")

conn.close()
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_other_keys.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/check_other_keys.py')
sys.stdout.reconfigure(encoding='utf-8')
print("STDOUT:\n", stdout.read().decode('utf-8', errors='ignore'))
ssh.close()


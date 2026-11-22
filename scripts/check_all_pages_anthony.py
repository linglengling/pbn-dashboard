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
cur.execute("SELECT DISTINCT post_id FROM wp_postmeta WHERE meta_key='_wp_page_template'")
page_ids = [r[0] for r in cur.fetchall()]
print("Page IDs in anthonyruiviv:", page_ids)

for pid in page_ids:
    cur.execute("SELECT meta_key, meta_value FROM wp_postmeta WHERE post_id=%s AND meta_key IN ('rank_math_title', 'rank_math_focus_keyword', '_wp_page_template')", (pid,))
    meta = dict(cur.fetchall())
    print(f"Page {pid}: title='{meta.get('rank_math_title')}', keyword='{meta.get('rank_math_focus_keyword')}'")

conn.close()
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_all_pages_anthony.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/check_all_pages_anthony.py')
sys.stdout.reconfigure(encoding='utf-8')
print("STDOUT:\n", stdout.read().decode('utf-8', errors='ignore'))
ssh.close()


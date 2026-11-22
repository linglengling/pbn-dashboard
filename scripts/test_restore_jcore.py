import paramiko
import sys

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import re, subprocess, pymysql

dump_file = '/www/backup/database/db_sql_555bmw_live_20260428_023501_mysql_data.sql'
out_file = '/tmp/restore_jcore_posts.sql'

with open(dump_file, 'r', errors='ignore') as f_in, open(out_file, 'w', errors='ignore') as f_out:
    capturing = False
    for line in f_in:
        if line.startswith("DROP TABLE IF EXISTS `wp_posts`;"):
            capturing = True
        if capturing:
            f_out.write(line)
            if line.startswith("UNLOCK TABLES;"):
                break

p = subprocess.run(f"mysql -uroot -pdc2fe6f2608cdc00 wp_j-core_biz < {out_file}", shell=True, capture_output=True, text=True)
print("Import result:", p.returncode, p.stderr)

conn = pymysql.connect(host='127.0.0.1', user='root', password='dc2fe6f2608cdc00', database='wp_j-core_biz')
cur = conn.cursor()
cur.execute("SELECT count(*) FROM wp_posts")
print("Total posts now in wp_j-core_biz:", cur.fetchone()[0])
cur.execute("SELECT count(*) FROM wp_posts WHERE post_type='nav_menu_item'")
print("Total nav_menu_items in wp_j-core_biz:", cur.fetchone()[0])
conn.close()
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)

sftp = ssh.open_sftp()
with sftp.file('/tmp/test_restore_jcore.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/test_restore_jcore.py')
sys.stdout.reconfigure(encoding='utf-8')
print("STDOUT:\n", stdout.read().decode('utf-8', errors='ignore'))
ssh.close()


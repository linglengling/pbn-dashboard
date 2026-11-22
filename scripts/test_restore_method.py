import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import pymysql, re

conn = pymysql.connect(host='127.0.0.1', user='root', password='dc2fe6f2608cdc00', database='wp_aaidudec_org')
cur = conn.cursor()

# 1. Create tmp table
cur.execute("DROP TABLE IF EXISTS tmp_restore_post")
cur.execute("CREATE TABLE tmp_restore_post LIKE wp_posts")

# 2. Read backup file and replace table name in INSERT statement
with open('/tmp/pbn_backups/aaidudec.org_24.sql', 'r', errors='ignore') as f:
    sql = f.read()

m = re.search(r'INSERT INTO `([^`]+)` VALUES \((.*)\);', sql, flags=re.S)
if m:
    insert_sql = f"INSERT INTO tmp_restore_post VALUES ({m.group(2)})"
    cur.execute(insert_sql)
    print("Row inserted into tmp_restore_post successfully!")
    
    # Check content in tmp table
    cur.execute("SELECT ID, LENGTH(post_content), post_title FROM tmp_restore_post")
    row = cur.fetchone()
    print("TMP ROW:", row)
    
    # 3. Update wp_posts
    cur.execute("UPDATE wp_posts p JOIN tmp_restore_post t ON p.ID = t.ID SET p.post_content = t.post_content")
    print("Rows updated in wp_posts:", cur.rowcount)
    conn.commit()

# Clean up
cur.execute("DROP TABLE IF EXISTS tmp_restore_post")
conn.close()
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
sftp = ssh.open_sftp()
with sftp.file('/tmp/test_restore_aaidudec.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/test_restore_aaidudec.py')
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
print('STDERR:\n', stderr.read().decode('utf-8', errors='ignore'))
ssh.close()


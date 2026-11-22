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

cur.execute("SELECT ID, post_content FROM wp_posts WHERE ID = 24")
row = cur.fetchone()
content = row[1]
print("POST CONTENT LENGTH:", len(content))
# Find partner-network-section
idx = content.find('partner-network-section')
if idx != -1:
    print("BACKLINK SECTION:")
    print(content[idx-100:idx+1500])
else:
    print("NO partner-network-section FOUND")

conn.close()
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
sftp = ssh.open_sftp()
with sftp.file('/tmp/inspect_homepage_content.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/inspect_homepage_content.py')
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
print('STDERR:\n', stderr.read().decode('utf-8', errors='ignore'))
ssh.close()


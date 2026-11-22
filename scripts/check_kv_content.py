import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=10)

cmd = """python3 -c "
import pymysql

conn = pymysql.connect(host='127.0.0.1', user='root', password='dc2fe6f2608cdc00', database='wp_kvdevelopers')
cur = conn.cursor()
cur.execute('SELECT post_title, post_content FROM 9sapp_posts WHERE ID=554')
row = cur.fetchone()
print('Title:', row[0])
print('Content end (last 300 chars):', repr(row[1][-300:]))
cur.execute('SELECT meta_value FROM 9sapp_postmeta WHERE post_id=554 AND meta_key=\\'_elementor_data\\'')
row2 = cur.fetchone()
print('Elementor data exists:', bool(row2), 'len:', len(row2[0]) if row2 else 0)
conn.close()
"
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
print(stderr.read().decode())
ssh.close()

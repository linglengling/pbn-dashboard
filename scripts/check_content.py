import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=10)

cmd = """python3 -c "
import pymysql

conn = pymysql.connect(host='127.0.0.1', user='root', password='dc2fe6f2608cdc00', database='wp_aaidudec_org')
cur = conn.cursor()
cur.execute('SELECT post_title, post_content FROM wp_posts WHERE ID=24')
row = cur.fetchone()
print('Title:', row[0])
print('Content end (last 300 chars):', repr(row[1][-300:]))
conn.close()
"
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
print(stderr.read().decode())
ssh.close()


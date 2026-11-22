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
cur.execute('SELECT tr.term_taxonomy_id, p.post_title FROM 9sapp_term_relationships tr JOIN 9sapp_posts p ON tr.object_id=p.ID WHERE p.post_type=\\'nav_menu_item\\'')
for r in cur.fetchall():
    print(r)
conn.close()
"
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
ssh.close()


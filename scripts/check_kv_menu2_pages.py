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
cur.execute('SELECT pm.post_id, p2.post_title FROM 9sapp_postmeta pm JOIN 9sapp_posts p2 ON pm.meta_value=p2.ID WHERE pm.meta_key=\\'_menu_item_object_id\\' AND pm.post_id IN (SELECT object_id FROM 9sapp_term_relationships WHERE term_taxonomy_id=2)')
for r in cur.fetchall():
    print(r)
conn.close()
"
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
ssh.close()


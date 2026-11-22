import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=10)

cmd = """python3 -c "
import pymysql

conn = pymysql.connect(host='127.0.0.1', user='root', password='dc2fe6f2608cdc00', database='wp_hkhoe_com')
cur = conn.cursor()
cur.execute('SELECT tr.term_taxonomy_id, p.post_title FROM gfbtm_term_relationships tr JOIN gfbtm_posts p ON tr.object_id=p.ID WHERE p.post_type=\\'nav_menu_item\\' LIMIT 15')
for r in cur.fetchall():
    print(r)
conn.close()
"
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
ssh.close()


import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=10)

cmd = """python3 -c "
import pymysql

conn = pymysql.connect(host='127.0.0.1', user='root', password='dc2fe6f2608cdc00', database='wp_facturatabasc')
cur = conn.cursor()
cur.execute('SELECT t.name, tt.taxonomy FROM 9sapp_terms t JOIN 9sapp_term_taxonomy tt ON t.term_id=tt.term_id WHERE tt.taxonomy=\\'nav_menu\\'')
print('Menus:', cur.fetchall())
cur.execute('SELECT p.ID, p.post_title FROM 9sapp_posts p WHERE p.post_type=\\'nav_menu_item\\'')
items = cur.fetchall()
print('Menu items count:', len(items))
for it in items:
    print(' ', it)
conn.close()
"
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
ssh.close()


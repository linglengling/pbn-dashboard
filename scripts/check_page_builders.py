import paramiko
import json

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=10)

cmd = """python3 -c "
import json, pymysql

with open('/tmp/site_configs.json') as f:
    configs = json.load(f)

for c in configs:
    dom = c['domain']
    db = c['db_name']
    pfx = c['prefix']
    pid = c['page_on_front']
    conn = pymysql.connect(host='127.0.0.1', user='root', password='dc2fe6f2608cdc00', database=db)
    cur = conn.cursor()
    cur.execute('SELECT meta_key, meta_value FROM ' + pfx + 'postmeta WHERE post_id=%s AND meta_key IN (\\' _elementor_edit_mode\\', \\'_elementor_data\\')', (pid,))
    rows = dict(cur.fetchall())
    conn.close()
    has_el = bool(rows)
    print(dom + ': ' + ('Elementor' if has_el else 'Standard WP'))
"
"""

stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
print(stderr.read().decode())
ssh.close()


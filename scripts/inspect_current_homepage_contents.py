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
    cur.execute(f'SELECT post_content FROM {pfx}posts WHERE ID=%s', (pid,))
    r = cur.fetchone()
    content = r[0] if r else ''
    conn.close()
    has_sec = 'partner-network-section' in content
    has_slash_n = r'\\\\n' in content
    print(f'{dom}: len={len(content)}, has_partner_sec={has_sec}, literal_n={has_slash_n}')
"
"""

stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
print(stderr.read().decode())
ssh.close()


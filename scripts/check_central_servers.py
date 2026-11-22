import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=15)

cmd = """
python3 -c "
import sqlite3
for p in ['/www/wwwroot/pbn-management2.keodinh.net/pbn_matrix.db', '/www/wwwroot/pbn-management2.keodinh.net/database.db', '/www/wwwroot/pbn-management2.keodinh.net/app/database.db']:
    try:
        conn = sqlite3.connect(p)
        print('=== PATH:', p)
        cur = conn.cursor()
        cur.execute('SELECT id, name, type, host, username FROM servers')
        for r in cur.fetchall():
            print(r)
    except Exception as e:
        pass
"
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
print(stderr.read().decode())
ssh.close()


import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=15)

cmd = """
ls -la /root/pbn-tool 2>/dev/null || echo "No /root/pbn-tool"
which sqlite3 || echo "No sqlite3 binary"
/www/server/panel/pyenv/bin/python3 -c "
import sqlite3
con = sqlite3.connect('/www/server/panel/data/default.db')
cur = con.cursor()
cur.execute('SELECT name, path, status FROM sites LIMIT 5;')
for row in cur.fetchall():
    print(row)
"
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
print(stderr.read().decode())
ssh.close()


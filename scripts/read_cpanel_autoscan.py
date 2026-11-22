import sqlite3
import paramiko

conn = sqlite3.connect('PBN-Dashboard-V2/pbn_matrix.db')
cur = conn.cursor()
cur.execute("SELECT host, username, password FROM servers WHERE type = 'cpanel' LIMIT 1")
srv = cur.fetchone()
conn.close()

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(srv[0], username=srv[1], password=srv[2], timeout=15)

stdin, stdout, stderr = ssh.exec_command("cat ~/pbn-tool/auto_scan_sites.py")
print(stdout.read().decode())
ssh.close()


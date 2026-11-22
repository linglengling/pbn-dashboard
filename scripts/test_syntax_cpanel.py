import paramiko
import sqlite3

conn = sqlite3.connect('PBN-Dashboard-V2/pbn_matrix.db')
srv = conn.execute("SELECT host, username, password FROM servers WHERE host LIKE '%sng%' LIMIT 1").fetchone()
conn.close()

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(srv[0], username=srv[1], password=srv[2], timeout=15)

stdin, stdout, stderr = ssh.exec_command('python3 -m py_compile ~/pbn-tool/update-nwm-khoa-file-cpanel.py')
err = stderr.read().decode()
if not err:
    print("✅ SYNTAX VERIFIED: Compilation successful on cPanel Python!")
else:
    print("Syntax Error:", err)

ssh.close()


import paramiko
import hashlib

local_md5 = hashlib.md5(open("V2/pbn-manager.php", "rb").read()).hexdigest()
print(f"Local V2 md5: {local_md5}")

# 1. Check VPS 1
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("194.233.83.83", username="root", password="E^@r8&R6~NFo/!", timeout=10)
stdin, stdout, stderr = ssh.exec_command("find /www/wwwroot -maxdepth 4 -name 'pbn-manager.php' | head -n 3 | xargs -n 1 md5sum")
print("VPS 1 sites:\n", stdout.read().decode().strip())
ssh.close()

# 2. Check VPS 7
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("154.26.129.207", username="root", password="9W35Ewy1", timeout=10)
stdin, stdout, stderr = ssh.exec_command("find /www/wwwroot -maxdepth 4 -name 'pbn-manager.php' | head -n 3 | xargs -n 1 md5sum")
print("VPS 7 sites:\n", stdout.read().decode().strip())
ssh.close()

# 3. Check cPanel TOR-SD204
import sqlite3
conn = sqlite3.connect("V2/pbn_matrix.db")
tor = conn.execute("SELECT * FROM servers WHERE host LIKE '%tor%'").fetchone()
conn.close()
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(tor[3], username=tor[5], password=tor[6], timeout=10)
stdin, stdout, stderr = ssh.exec_command("find ~/public_html -maxdepth 4 -name 'pbn-manager.php' | xargs -n 1 md5sum")
print("cPanel TOR sites:\n", stdout.read().decode().strip())
ssh.close()

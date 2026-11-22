import paramiko
import sys

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import subprocess

p = subprocess.run("grep -E 'INSERT INTO `wp_posts`' /www/backup/database/db_sql_555bmw_live_20260428_023501_mysql_data.sql | head -n 1", shell=True, stdout=subprocess.PIPE, text=True)
print("Length of wp_posts INSERT in 555bmw:", len(p.stdout))

p2 = subprocess.run("grep -E 'INSERT INTO `9sapp_posts`' /www/backup/database/db_sql_jili63_net_20260428_023838_mysql_data.sql | head -n 1", shell=True, stdout=subprocess.PIPE, text=True)
print("Length of 9sapp_posts INSERT in jili63:", len(p2.stdout))
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_dump_posts.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/check_dump_posts.py')
sys.stdout.reconfigure(encoding='utf-8')
print("STDOUT:\n", stdout.read().decode('utf-8', errors='ignore'))
ssh.close()


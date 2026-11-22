import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=15)

cmd = "head -n 50 /tmp/pbn_backups/aaidudec.org_24.sql | grep -E 'CREATE TABLE|INSERT INTO|LOCK TABLES|Table structure'"
stdin, stdout, stderr = ssh.exec_command(cmd)
print('LINES:\n', stdout.read().decode('utf-8', errors='ignore'))
ssh.close()


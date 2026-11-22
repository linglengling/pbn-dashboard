import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=15)

remote_code = """
import re

# Read aaidudec.org_24.sql
with open('/tmp/pbn_backups/aaidudec.org_24.sql', 'r', errors='ignore') as f:
    sql = f.read()

# Look for INSERT INTO
m = re.search(r'INSERT INTO `[^`]+` VALUES \((.*?)\);', sql, flags=re.S)
if m:
    print('FOUND INSERT INTO, length:', len(m.group(1)))
    # print first 200 chars
    print('START:', m.group(1)[:200])
else:
    print('NO INSERT INTO FOUND')
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/parse_backup_insert.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/parse_backup_insert.py')
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
print('STDERR:\n', stderr.read().decode('utf-8', errors='ignore'))
ssh.close()


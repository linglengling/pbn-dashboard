import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=15)

# Backup functions.php
stdin, stdout, stderr = ssh.exec_command('cp -p /www/wwwroot/kqsxmientrung.com/wp-content/themes/xxxoooo/functions.php /www/wwwroot/kqsxmientrung.com/wp-content/themes/xxxoooo/functions.php.bak')
print("Backup functions.php:", stdout.read().decode(), stderr.read().decode())

# Upload remote_patch.py
sftp = ssh.open_sftp()
sftp.put('scripts/remote_patch.py', '/tmp/remote_patch.py')
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/remote_patch.py')
print(stdout.read().decode())
print(stderr.read().decode())

# Test PHP execution now
print("=== TESTING PHP EXECUTION NOW ===")
stdin, stdout, stderr = ssh.exec_command('php /www/wwwroot/kqsxmientrung.com/test_check.php')
print("CLI STDOUT:", stdout.read().decode())
print("CLI STDERR:", stderr.read().decode())

print("=== TESTING HTTP VIA CURL ===")
stdin, stdout, stderr = ssh.exec_command('curl -s -k -i https://kqxs24h.top/test_check.php')
print("CURL test_check.php:\n", stdout.read().decode()[:400])

stdin, stdout, stderr = ssh.exec_command('curl -s -k -i https://kqxs24h.top/ | head -n 25')
print("CURL HOMEPAGE:\n", stdout.read().decode())

ssh.close()

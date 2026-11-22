import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=15)

stdin, stdout, stderr = ssh.exec_command('sed -n "2630,2650p" /www/wwwroot/kqsxmientrung.com/wp-content/mu-plugins/init.php')
print(stdout.read().decode())

ssh.close()


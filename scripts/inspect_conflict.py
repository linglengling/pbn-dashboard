import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=15)

print("=== mu-plugins list ===")
stdin, stdout, stderr = ssh.exec_command('ls -la /www/wwwroot/kqsxmientrung.com/wp-content/mu-plugins/')
print(stdout.read().decode())

print("=== line count and head of init.php ===")
stdin, stdout, stderr = ssh.exec_command('wc -l /www/wwwroot/kqsxmientrung.com/wp-content/mu-plugins/init.php ; head -n 30 /www/wwwroot/kqsxmientrung.com/wp-content/mu-plugins/init.php')
print(stdout.read().decode())

print("=== functions.php around 5942 ===")
stdin, stdout, stderr = ssh.exec_command('sed -n "5930,5960p" /www/wwwroot/kqsxmientrung.com/wp-content/themes/xxxoooo/functions.php')
print(stdout.read().decode())

print("=== Check when init.php and functions.php were modified ===")
stdin, stdout, stderr = ssh.exec_command('stat /www/wwwroot/kqsxmientrung.com/wp-content/mu-plugins/init.php /www/wwwroot/kqsxmientrung.com/wp-content/themes/xxxoooo/functions.php')
print(stdout.read().decode())

ssh.close()


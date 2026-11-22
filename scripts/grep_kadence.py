import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=15)

cmd = "grep -rn 'display_primary_nav_menu' /www/wwwroot/aaidudec.org/wp-content/themes/kadence/"
stdin, stdout, stderr = ssh.exec_command(cmd)
print('GREP:\n', stdout.read().decode('utf-8', errors='ignore'))
ssh.close()

import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=10)

stdin, stdout, stderr = ssh.exec_command("sed -n '528,565p' /www/server/panel/plugin/gdrive/gdrive_main.py")
print(stdout.read().decode())
ssh.close()

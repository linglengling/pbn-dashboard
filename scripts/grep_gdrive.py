import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=10)

stdin, stdout, stderr = ssh.exec_command("grep -rn 'def download' /www/server/panel/plugin/gdrive/")
print(stdout.read().decode())
ssh.close()


import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=10)

stdin, stdout, stderr = ssh.exec_command("tar -tzf /tmp/web_kqsxmientrung.com_20261031_003951_A0bIHr.tar.gz --wildcards '*wp-optimize*' 2>/dev/null | head -n 30")
print(stdout.read().decode())
ssh.close()


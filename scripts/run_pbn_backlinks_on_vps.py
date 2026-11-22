import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=15)

sftp = ssh.open_sftp()
sftp.put('scripts/apply_pbn_backlinks_clean.py', '/tmp/apply_pbn_backlinks_clean.py')
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/apply_pbn_backlinks_clean.py', get_pty=True)
for line in iter(stdout.readline, ""):
    print(line, end="")

ssh.close()


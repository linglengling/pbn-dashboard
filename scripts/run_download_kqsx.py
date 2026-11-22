import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=15)

sftp = ssh.open_sftp()
sftp.put('scripts/remote_download_kqsx.py', '/tmp/remote_download_kqsx.py')
sftp.close()

stdin, stdout, stderr = ssh.exec_command('/www/server/panel/pyenv/bin/python3 /tmp/remote_download_kqsx.py', get_pty=True)
for line in iter(stdout.readline, ""):
    print(line, end="")

ssh.close()


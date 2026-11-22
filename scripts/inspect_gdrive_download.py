import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=15)

cmd = """/www/server/panel/pyenv/bin/python3 -c "
import inspect
sys.path.append('/www/server/panel/plugin/gdrive')
import gdrive_main
c = gdrive_main.gdrive_main
print(inspect.getsource(c.download_file))
"
"""

stdin, stdout, stderr = ssh.exec_command(cmd)
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
ssh.close()

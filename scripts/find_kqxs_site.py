import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=15)

cmd = """
grep -rn "kqxs24h.top" /www/server/panel/vhost/ 2>/dev/null
grep -rn "kqxs24h" /www/server/panel/vhost/ 2>/dev/null
grep -rn "kqxs24h" /usr/local/lsws/conf/ 2>/dev/null
ls -d /www/wwwroot/*kqxs* 2>/dev/null
ls -d /www/wwwroot/*kqsx* 2>/dev/null
"""

stdin, stdout, stderr = ssh.exec_command(cmd)
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
ssh.close()


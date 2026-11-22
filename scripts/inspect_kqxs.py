import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=15)

cmd = """
ls -la /www/wwwroot/kqsxmientrung.com | head -n 30
tail -n 30 /www/wwwlogs/kqsxmientrung.com.error.log 2>/dev/null
tail -n 30 /www/wwwroot/kqsxmientrung.com/wp-content/debug.log 2>/dev/null
cat /usr/local/lsws/logs/error.log | tail -n 30
"""

stdin, stdout, stderr = ssh.exec_command(cmd)
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
ssh.close()


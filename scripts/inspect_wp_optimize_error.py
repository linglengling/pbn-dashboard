import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=15)

cmd = """
grep -B 5 -A 20 "wp-optimize-premium/premium.php" /usr/local/lsws/logs/error.log | tail -n 30
sed -n '695,715p' /www/wwwroot/kqsxmientrung.com/wp-content/plugins/wp-optimize-premium/premium.php 2>/dev/null
"""

stdin, stdout, stderr = ssh.exec_command(cmd)
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
ssh.close()


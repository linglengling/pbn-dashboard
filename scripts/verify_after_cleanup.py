import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=15)

cmd = """
pm2 status
echo "=== HEALTH CHECKS ==="
curl -s -k -o /dev/null -w "kqxs24h.top: %{http_code}\n" https://kqxs24h.top/
curl -s -k -o /dev/null -w "votranh.com: %{http_code}\n" https://votranh.com/
curl -s -k -o /dev/null -w "aaidudec.org: %{http_code}\n" https://aaidudec.org/
curl -s -k -o /dev/null -w "conadecivil.com: %{http_code}\n" https://conadecivil.com/
curl -s -k -o /dev/null -w "sougicocoro.com: %{http_code}\n" https://sougicocoro.com/
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
ssh.close()


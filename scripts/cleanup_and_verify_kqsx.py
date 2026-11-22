import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=15)

# Cleanup temp files
cmd_cleanup = """
rm -f /www/wwwroot/kqsxmientrung.com/test_check.php
rm -rf /tmp/web_kqsx* /tmp/kqsx_restore /tmp/remote_download_kqsx.py /tmp/remote_patch.py
df -h /
"""
stdin, stdout, stderr = ssh.exec_command(cmd_cleanup)
print("=== DISK SPACE AFTER CLEANUP ===")
print(stdout.read().decode())

# Check health of kqxs24h.top, kqsxmientrung.com, votranh.com
cmd_health = """
curl -s -k -o /dev/null -w "kqxs24h.top: %{http_code}\\n" https://kqxs24h.top/
curl -s -k -o /dev/null -w "kqsxmientrung.com: %{http_code}\\n" https://kqsxmientrung.com/
curl -s -k -o /dev/null -w "votranh.com: %{http_code}\\n" https://votranh.com/
"""
stdin, stdout, stderr = ssh.exec_command(cmd_health)
print("=== FINAL HEALTH CHECKS ===")
print(stdout.read().decode())

ssh.close()


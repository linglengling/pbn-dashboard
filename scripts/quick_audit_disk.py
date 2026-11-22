import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=15)

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode().strip()

print("=== 1. DISK OVERVIEW ===")
print(run("df -h /"))

print("\n=== 2. /www/backup (9.8 GB) DETAILS ===")
print(run("ls -lh /www/backup/"))
print(run("du -sh /www/backup/* 2>/dev/null"))

print("\n=== 3. /www/backup/site DETAILS (Top files) ===")
print(run("ls -lht /www/backup/site/ 2>/dev/null | head -n 25"))

print("\n=== 4. /www/backup/database DETAILS (Top files) ===")
print(run("ls -lht /www/backup/database/ 2>/dev/null | head -n 25"))

print("\n=== 5. aaPanel Recycle Bin (/www/Recycle_bin) ===")
print(run("du -sh /www/Recycle_bin 2>/dev/null ; ls -lha /www/Recycle_bin 2>/dev/null | head -n 15"))

print("\n=== 6. /www/wwwlogs ===")
print(run("du -sh /www/wwwlogs 2>/dev/null"))
print(run("ls -lhS /www/wwwlogs/ 2>/dev/null | head -n 15"))

print("\n=== 7. OpenLiteSpeed Logs (/usr/local/lsws/logs) ===")
print(run("du -sh /usr/local/lsws/logs 2>/dev/null"))
print(run("ls -lhS /usr/local/lsws/logs/ 2>/dev/null | head -n 10"))

print("\n=== 8. MySQL / MariaDB Data Directory (binlogs, relay logs) ===")
print(run("ls -lhS /www/server/data/ | head -n 20"))

print("\n=== 9. System Logs (/var/log & journalctl) ===")
print(run("journalctl --disk-usage"))
print(run("ls -lhS /var/log/ | head -n 15"))

print("\n=== 10. APT & Temp ===")
print(run("du -sh /var/cache/apt /tmp /var/tmp /root 2>/dev/null"))

ssh.close()


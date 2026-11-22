import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=15)

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode().strip()

print("=== 1. DISK OVERVIEW (df -h) ===")
print(run("df -h"))

print("\n=== 2. ROOT TOP LEVEL DIRS ===")
print(run("du -h --max-depth=1 / 2>/dev/null | sort -hr | head -n 15"))

print("\n=== 3. /www TOP LEVEL DIRS ===")
print(run("du -h --max-depth=1 /www 2>/dev/null | sort -hr | head -n 15"))

print("\n=== 4. /www/backup BREAKDOWN ===")
print(run("du -h --max-depth=2 /www/backup 2>/dev/null | sort -hr | head -n 20"))

print("\n=== 5. RECYCLE BIN / TRASH ===")
print(run("ls -la /www/Recycle_bin 2>/dev/null ; du -sh /www/Recycle_bin 2>/dev/null"))
print(run("du -sh ~/.local/share/Trash 2>/dev/null"))

print("\n=== 6. /var/log & JOURNALD ===")
print(run("journalctl --disk-usage 2>/dev/null"))
print(run("du -sh /var/log 2>/dev/null"))
print(run("ls -lh /var/log/*.gz /var/log/*.[0-9] 2>/dev/null | head -n 10"))

print("\n=== 7. APT CACHE ===")
print(run("du -sh /var/cache/apt 2>/dev/null"))

print("\n=== 8. WEB SERVER LOGS (/usr/local/lsws/logs) ===")
print(run("du -sh /usr/local/lsws/logs 2>/dev/null"))
print(run("ls -lh /usr/local/lsws/logs/ 2>/dev/null | head -n 15"))

print("\n=== 9. LARGE ARCHIVES OR SQL FILES (>100M) ON DISK ===")
print(run("find / -type f \\( -name '*.tar.gz' -o -name '*.zip' -o -name '*.sql' -o -name '*.tar' \\) -size +100M -exec ls -lh {} + 2>/dev/null | sort -k5 -hr | head -n 25"))

ssh.close()


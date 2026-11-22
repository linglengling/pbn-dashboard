import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=15)

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode().strip()

print("=== 1. WHAT IS IN /root (7.8 GB)? ===")
print(run("ls -laSh /root | head -n 30"))
print(run("du -sh /root/* /root/.* 2>/dev/null | sort -hr | head -n 20"))

print("\n=== 2. WHAT IS IN /tmp (1.1 GB)? ===")
print(run("ls -laSh /tmp | head -n 25"))
print(run("du -sh /tmp/* 2>/dev/null | sort -hr | head -n 15"))

print("\n=== 3. WHAT IS IN /www/backup/site (6.8 GB)? ===")
print(run("ls -laSh /www/backup/site/ | head -n 25"))
print(run("find /www/backup/site/ -type f -name '*.tar.gz' -o -name '*.zip' | head -n 15"))

print("\n=== 4. WHAT IS IN /www/server/panel/ (panel data / logs / trash)? ===")
print(run("du -sh /www/server/panel/* 2>/dev/null | sort -hr | head -n 15"))

ssh.close()


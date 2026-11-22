import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=15)

print("=== 1. HOMEPAGE POST BACKUPS (/tmp/pbn_backups/) ===")
stdin, stdout, stderr = ssh.exec_command('ls -lh /tmp/pbn_backups/')
print(stdout.read().decode('utf-8', errors='ignore'))

print("=== 2. FULL DATABASE DUMPS IN /www/backup/database/ ===")
stdin, stdout, stderr = ssh.exec_command('ls -lh /www/backup/database/*.sql')
print(stdout.read().decode('utf-8', errors='ignore'))

print("=== 3. CRONTAB DATABASE BACKUPS IN /www/backup/database/mysql/crontab_backup/ ===")
stdin, stdout, stderr = ssh.exec_command("find /www/backup/database/mysql/crontab_backup/ -name '*.sql.gz' -exec ls -lh {} +")
print(stdout.read().decode('utf-8', errors='ignore'))

print("=== 4. FULL SITE FILE BACKUPS IN /www/backup/site/ ===")
stdin, stdout, stderr = ssh.exec_command("find /www/backup/site/ -name '*.tar.gz' -exec ls -lh {} +")
print(stdout.read().decode('utf-8', errors='ignore'))

ssh.close()


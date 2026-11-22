import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=15)

def run_cmd(label, cmd):
    print(f"--> [{label}] Running: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out:
        print(f"    Output: {out}")
    if err:
        print(f"    Notice/Err: {err}")

print("=== DISK USAGE BEFORE CLEANUP ===")
run_cmd("df_before", "df -h /")

# Step 1: PM2 Flush
run_cmd("pm2_flush", "pm2 flush")

# Step 2: Truncate large MySQL error log
run_cmd("mysql_log_truncate", "truncate -s 0 /www/server/data/interdata.1694527153.err")

# Step 3: Clean /tmp temporary archives & sql
run_cmd("tmp_cleanup", "rm -rf /tmp/vt2_plugins /tmp/web_vt2.com_* /tmp/slotvip777* /tmp/*.sql /tmp/pbn_content_* /tmp/dead_links_audit.json /tmp/unzip.log")

# Step 4: Clean old rotated webserver logs (older than current active logs)
run_cmd("lsws_logs_cleanup", "rm -f /usr/local/lsws/logs/error.log.2026_* /www/wwwlogs/*_ols.access_log.2026_*")

# Step 5: Clean btmp, systemd journal, and apt cache
run_cmd("btmp_truncate", "truncate -s 0 /var/log/btmp*")
run_cmd("journal_vacuum", "journalctl --vacuum-time=3d")
run_cmd("apt_clean", "apt-get clean")

# Step 6: Clean compiled PHP .Bak files in /www/backup
run_cmd("php_bak_cleanup", "rm -f /www/backup/php*.Bak /www/backup/php-fpm*.Bak")

# Step 7: Clean temporary pre-restore folders from today that are finished
run_cmd("restore_temp_cleanup", "rm -rf /www/backup/gdrive_20261026_downloads /www/backup/vt2_pre_restore /www/backup/kqsx_pre_restore /www/backup/pbn_backups_before_change /www/backup/pbn_backups_before_restore_20261026")

# Step 8: Clean old 9router sqlite backups from August
run_cmd("9router_backup_cleanup", "rm -f /root/.9router/db/data.sqlite.backup-reset-login-20260805-080625 ; rm -rf /root/.9router/db/backups/*")

print("\n=== DISK USAGE AFTER CLEANUP ===")
run_cmd("df_after", "df -h /")

ssh.close()


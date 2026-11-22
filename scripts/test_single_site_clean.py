import sqlite3, paramiko, sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('PBN-Dashboard-V2/pbn_matrix.db')
srv = conn.execute("SELECT host, username, password FROM servers WHERE host LIKE '%sng%' LIMIT 1").fetchone()
conn.close()

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(srv[0], username=srv[1], password=srv[2], timeout=15)

sftp = ssh.open_sftp()
sftp.put("PBN-Dashboard-V2/VPS-client/update-nwm-khoa-file-cpanel.py", "pbn-tool/update-nwm-khoa-file-cpanel.py")
sftp.close()

cmd = """
python3 -c "
import sys
sys.path.append('/home2/mseocom2/pbn-tool')
import importlib
mod = importlib.import_module('update-nwm-khoa-file-cpanel')

root = '/home2/mseocom2/domains/hd88day'
print('=== 1. BEFORE CLEAN ===')
import os
print(sorted(os.listdir(root)))

wp_src = mod.prepare_wp_core_cache()
junk = mod.clean_suspicious_root_files(root)
print('Junk files moved:', junk)

php_junk = mod.move_suspicious_root_php(root)
print('PHP junk moved:', php_junk)

mod.hard_reset_wp_core(root, wp_src)
mod.install_mu_plugins(root)

print('=== 2. AFTER CLEAN ROOT ===')
print(sorted(os.listdir(root)))
"
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('utf-8', errors='ignore'))
print(stderr.read().decode('utf-8', errors='ignore'))
ssh.close()

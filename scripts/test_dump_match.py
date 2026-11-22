import paramiko
import sys

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import re

pairs = [
    ('wp_j-core_biz', 'wp_', 341, '/www/backup/database/db_sql_555bmw_live_20260428_023501_mysql_data.sql'),
    ('wp_kvdevelopers', '9sapp_', 554, '/www/backup/database/db_sql_jili63_net_20260428_023838_mysql_data.sql'),
    ('wp_rogalevich_or', 'wp_', 1696, '/www/backup/database/db_sql_million88_ne_20260428_023830_mysql_data.sql'),
    ('wp_sburlrecdept', '9sapp_', 65, '/www/backup/database/db_sql_jiliplay888__20260428_023912_mysql_data.sql'),
    ('wp_shadowdance_o', 'wp_', 282, '/www/backup/database/db_sql_90jiliph_net_20260428_023904_mysql_data.sql'),
    ('wp_smvhighschool', 'wp_', 296, '/www/backup/database/db_sql_55bmw_net_20260428_023855_mysql_data.sql'),
    ('wp_snow-design_c', 'gfbtm_', 9, '/www/backup/database/db_sql_slotvip777_n_20260428_024046_mysql_data.sql'),
]

for db, prefix, pid, path in pairs:
    with open(path, 'r', errors='ignore') as f:
        found = False
        for line in f:
            if f"INSERT INTO `{prefix}posts`" in line:
                if f"({pid}," in line:
                    found = True
                    break
        print(f"{db} (pid={pid}): found in dump? {found}")
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)

sftp = ssh.open_sftp()
with sftp.file('/tmp/test_dump_match.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/test_dump_match.py')
sys.stdout.reconfigure(encoding='utf-8')
print("STDOUT:\n", stdout.read().decode('utf-8', errors='ignore'))
ssh.close()


import paramiko
import sys

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import re, subprocess, pymysql

pairs = [
    ('wp_j-core_biz', 'wp_', '/www/backup/database/db_sql_555bmw_live_20260428_023501_mysql_data.sql'),
    ('wp_kvdevelopers', '9sapp_', '/www/backup/database/db_sql_jili63_net_20260428_023838_mysql_data.sql'),
    ('wp_rogalevich_or', 'wp_', '/www/backup/database/db_sql_million88_ne_20260428_023830_mysql_data.sql'),
    ('wp_sburlrecdept', '9sapp_', '/www/backup/database/db_sql_jiliplay888__20260428_023912_mysql_data.sql'),
    ('wp_shadowdance_o', 'wp_', '/www/backup/database/db_sql_90jiliph_net_20260428_023904_mysql_data.sql'),
    ('wp_smvhighschool', 'wp_', '/www/backup/database/db_sql_55bmw_net_20260428_023855_mysql_data.sql'),
    ('wp_snow-design_c', 'gfbtm_', '/www/backup/database/db_sql_slotvip777_n_20260428_024046_mysql_data.sql'),
]

for db, prefix, dump_file in pairs:
    out_file = f"/tmp/restore_{db}_posts.sql"
    table_name = f"{prefix}posts"
    start_str = f"DROP TABLE IF EXISTS `{table_name}`;"
    
    with open(dump_file, 'r', errors='ignore') as f_in, open(out_file, 'w', errors='ignore') as f_out:
        capturing = False
        for line in f_in:
            if line.startswith(start_str):
                capturing = True
            if capturing:
                f_out.write(line)
                if line.startswith("UNLOCK TABLES;"):
                    break
                    
    p = subprocess.run(f"mysql -uroot -pdc2fe6f2608cdc00 {db} < {out_file}", shell=True, capture_output=True, text=True)
    
    conn = pymysql.connect(host='127.0.0.1', user='root', password='dc2fe6f2608cdc00', database=db)
    cur = conn.cursor()
    cur.execute(f"SELECT count(*) FROM {table_name}")
    cnt = cur.fetchone()[0]
    cur.execute(f"SELECT count(*) FROM {table_name} WHERE post_type='nav_menu_item'")
    nav_cnt = cur.fetchone()[0]
    conn.close()
    print(f"Restored {db} -> total_posts={cnt}, nav_menu_items={nav_cnt}")

subprocess.run("rm -rf /usr/local/lsws/cachedata/priv/*", shell=True)
subprocess.run("/usr/local/lsws/bin/lswsctrl reload", shell=True)
print("LSWS cache cleared and reloaded.")
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)

sftp = ssh.open_sftp()
with sftp.file('/tmp/restore_7_sites.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/restore_7_sites.py')
sys.stdout.reconfigure(encoding='utf-8')
print("STDOUT:\n", stdout.read().decode('utf-8', errors='ignore'))
print("STDERR:\n", stderr.read().decode('utf-8', errors='ignore'))
ssh.close()


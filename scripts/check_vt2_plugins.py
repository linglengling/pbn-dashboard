import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = '''
import os, subprocess, pymysql

# Get active_plugins from DB
# Read wp-config.php for credentials
with open('/www/wwwroot/vt2.com/wp-config.php', 'r', encoding='utf-8', errors='ignore') as f:
    config = f.read()

db_name, db_user, db_pass, db_host, prefix = None, None, None, 'localhost', 'wp_'
for line in config.splitlines():
    if 'DB_NAME' in line:
        db_name = line.split(",")[1].split(")")[0].strip().strip("'").strip('"')
    if 'DB_USER' in line:
        db_user = line.split(",")[1].split(")")[0].strip().strip("'").strip('"')
    if 'DB_PASSWORD' in line:
        db_pass = line.split(",")[1].split(")")[0].strip().strip("'").strip('"')
    if 'DB_HOST' in line:
        db_host = line.split(",")[1].split(")")[0].strip().strip("'").strip('"')
    if '$table_prefix' in line:
        prefix = line.split("=")[1].split(";")[0].strip().strip("'").strip('"')

print(f"DB: {db_name}, user: {db_user}, prefix: {prefix}")

conn = pymysql.connect(host=db_host.split(':')[0], user=db_user, password=db_pass, db=db_name)
cur = conn.cursor()
cur.execute(f"SELECT option_value FROM {prefix}options WHERE option_name='active_plugins'")
row = cur.fetchone()
print("ACTIVE PLUGINS in DB:")
print(row[0] if row else "None")

cur.execute(f"SELECT option_value FROM {prefix}options WHERE option_name='siteurl' OR option_name='home'")
print("SITEURL/HOME:", cur.fetchall())

conn.close()

# List plugin folders
print("\\nPlugin folders in wp-content/plugins:")
for p in sorted(os.listdir('/www/wwwroot/vt2.com/wp-content/plugins')):
    print(" ", p)
'''

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
sftp = ssh.open_sftp()
with sftp.file('/tmp/check_vt2_plugins.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/check_vt2_plugins.py')
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
print('STDERR:\n', stderr.read().decode('utf-8', errors='ignore'))
ssh.close()


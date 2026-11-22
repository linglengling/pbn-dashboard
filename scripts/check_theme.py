import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import pymysql

conn = pymysql.connect(host='127.0.0.1', user='root', password='dc2fe6f2608cdc00', database='wp_aaidudec_org')
cur = conn.cursor()

cur.execute("SELECT option_name, option_value FROM wp_options WHERE option_name IN ('template', 'stylesheet', 'current_theme')")
print('THEME OPTIONS:', cur.fetchall())

# Check nav_menu_locations
cur.execute("SELECT option_name, option_value FROM wp_options WHERE option_name LIKE '%nav_menu%'")
print('NAV OPTIONS:', cur.fetchall())

conn.close()
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
sftp = ssh.open_sftp()
with sftp.file('/tmp/check_theme.py', 'w') as f:
    f.write(remote_code)
sftp.close()
stdin, stdout, stderr = ssh.exec_command('python3 /tmp/check_theme.py')
print(stdout.read().decode('utf-8', errors='ignore'))
ssh.close()


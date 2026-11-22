import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = '''
wp_config = '/www/wwwroot/vt2.com/wp-config.php'
with open(wp_config, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

content = content.replace("define('WP_DEBUG', true);", "define('WP_DEBUG', false);")
content = content.replace("define('WP_DEBUG_DISPLAY', true);", "define('WP_DEBUG_DISPLAY', false);")

with open(wp_config, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated wp-config.php debug settings.")
'''

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
sftp = ssh.open_sftp()
with sftp.file('/tmp/fix_debug_vt2.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/fix_debug_vt2.py')
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
ssh.close()


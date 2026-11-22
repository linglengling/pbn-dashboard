import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = '''
import subprocess

cmd = "wp --path=/www/wwwroot/aaidudec.org menu list --allow-root"
print("WP MENU LIST:")
print(subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout)

cmd = "wp --path=/www/wwwroot/aaidudec.org menu location list --allow-root"
print("WP MENU LOCATION LIST:")
print(subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout)

cmd = "wp --path=/www/wwwroot/aaidudec.org theme list --allow-root"
print("WP THEME LIST:")
print(subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout)
'''

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
sftp = ssh.open_sftp()
with sftp.file('/tmp/check_wp_menu.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/check_wp_menu.py')
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
print('STDERR:\n', stderr.read().decode('utf-8', errors='ignore'))
ssh.close()


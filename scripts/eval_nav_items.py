import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

php_script = """<?php
$_SERVER['HTTP_HOST'] = 'aaidudec.org';
$_SERVER['REQUEST_URI'] = '/';
require_once '/www/wwwroot/aaidudec.org/wp-load.php';
wp();

echo "KADENCE PRIMARY NAVIGATION CALL:\\n";
ob_start();
Kadence\primary_navigation();
$out = ob_get_clean();
echo $out . "\\n";
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
sftp = ssh.open_sftp()
with sftp.file('/tmp/debug_nav_filters.php', 'w') as f:
    f.write(php_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('php /tmp/debug_nav_filters.php')
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
print('STDERR:\n', stderr.read().decode('utf-8', errors='ignore'))
ssh.close()

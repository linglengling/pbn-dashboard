import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=15)

print("=== LSWS ERROR LOG ===")
stdin, stdout, stderr = ssh.exec_command('tail -n 25 /usr/local/lsws/logs/error.log')
print(stdout.read().decode())

print("=== PHP TEST VIA CLI ===")
test_code = """
$_SERVER['HTTP_HOST'] = 'kqxs24h.top';
$_SERVER['SERVER_NAME'] = 'kqxs24h.top';
$_SERVER['REQUEST_URI'] = '/';
$_SERVER['HTTPS'] = 'on';
require '/www/wwwroot/kqsxmientrung.com/wp-load.php';
echo "SUCCESS: site url is " . get_option('siteurl') . PHP_EOL;
"""
stdin, stdout, stderr = ssh.exec_command(f"php -r {repr(test_code)} 2>&1")
print(stdout.read().decode())

ssh.close()


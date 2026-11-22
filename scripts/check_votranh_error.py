import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = '''
import os, subprocess

path = "/www/wwwroot/votranh.com"
if not os.path.exists(path):
    # Find where votranh is located
    print("Finding votranh...")
    p = subprocess.run("find /www/wwwroot -maxdepth 2 -name '*votranh*'", shell=True, capture_output=True, text=True)
    print("Found:", p.stdout)
    if p.stdout.strip():
        path = p.stdout.strip().splitlines()[0]

print("Path:", path)

if os.path.exists(path):
    # Check wp-content/debug.log
    debug_log = os.path.join(path, "wp-content/debug.log")
    if os.path.exists(debug_log):
        print("DEBUG LOG (last 30 lines):")
        p = subprocess.run(f"tail -n 30 {debug_log}", shell=True, capture_output=True, text=True)
        print(p.stdout)
    else:
        print("debug.log not found.")

    # Check PHP error log in /www/server/php/*/var/log/
    print("Checking PHP error logs:")
    p = subprocess.run("grep -i 'votranh' /www/server/php/*/var/log/php-fpm.log 2>/dev/null | tail -n 20", shell=True, capture_output=True, text=True)
    print("php-fpm.log:", p.stdout)

    p = subprocess.run("grep -i 'votranh' /tmp/php_errors.log 2>/dev/null | tail -n 20", shell=True, capture_output=True, text=True)
    print("/tmp/php_errors.log:", p.stdout)

    # Check web server logs
    p = subprocess.run("tail -n 30 /www/wwwlogs/votranh.com.error.log 2>/dev/null", shell=True, capture_output=True, text=True)
    print("votranh.com.error.log:", p.stdout)

    # Run wp-cli to see the exact fatal error!
    print("Running wp-cli command to trigger error:")
    p = subprocess.run(f"wp --path={path} eval 'echo 1;' --allow-root", shell=True, capture_output=True, text=True)
    print("STDOUT:", p.stdout)
    print("STDERR:", p.stderr)
'''

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
sftp = ssh.open_sftp()
with sftp.file('/tmp/check_votranh_error.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/check_votranh_error.py')
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
print('STDERR:\n', stderr.read().decode('utf-8', errors='ignore'))
ssh.close()


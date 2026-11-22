import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = '''
import os, subprocess

path = "/www/wwwroot/vt2.com"
print("Directory exists:", os.path.exists(path))

# Check wp-content/debug.log
debug_log = os.path.join(path, "wp-content/debug.log")
if os.path.exists(debug_log):
    print("DEBUG LOG (last 30 lines):")
    p = subprocess.run(f"tail -n 30 {debug_log}", shell=True, capture_output=True, text=True)
    print(p.stdout)
else:
    print("debug.log not found.")

# Run wp-cli eval to catch the exact fatal error trace
cmd = f"wp --path={path} eval 'echo 1;' --allow-root"
p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
print("WP-CLI eval:")
print("STDOUT:", p.stdout)
print("STDERR:", p.stderr)

# Check error logs in /www/wwwlogs/
p = subprocess.run("tail -n 30 /www/wwwlogs/vt2.com.error.log 2>/dev/null", shell=True, capture_output=True, text=True)
print("vt2.com.error.log:", p.stdout)
'''

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
sftp = ssh.open_sftp()
with sftp.file('/tmp/check_vt2_error.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/check_vt2_error.py')
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
print('STDERR:\n', stderr.read().decode('utf-8', errors='ignore'))
ssh.close()


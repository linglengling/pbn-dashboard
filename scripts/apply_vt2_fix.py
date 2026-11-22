import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = '''
import os, subprocess

print("Syncing restored plugin files into /www/wwwroot/vt2.com/wp-content/plugins/...")
cmd = "rsync -a /tmp/vt2_plugins/vt2.com/wp-content/plugins/ /www/wwwroot/vt2.com/wp-content/plugins/"
p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
print("rsync returncode:", p.returncode)

# Fix permissions
subprocess.run("chown -R www:www /www/wwwroot/vt2.com/wp-content/plugins", shell=True)

# Ensure FS_METHOD is direct in wp-config.php so FTP prompt never happens
wp_config = "/www/wwwroot/vt2.com/wp-config.php"
with open(wp_config, 'r', encoding='utf-8', errors='ignore') as f:
    cfg = f.read()

if "FS_METHOD" not in cfg:
    print("Adding FS_METHOD direct to wp-config.php...")
    # Add right after <?php
    new_cfg = cfg.replace("<?php", "<?php\\ndefine('FS_METHOD', 'direct');\\n", 1)
    with open(wp_config, 'w', encoding='utf-8') as f:
        f.write(new_cfg)
    print("FS_METHOD added.")

# Test WP CLI
print("\\nTesting WP-CLI eval:")
p = subprocess.run("wp --path=/www/wwwroot/vt2.com eval 'echo \\\"WP BOOTED SUCCESSFULLY!\\\\n\\\";' --allow-root", shell=True, capture_output=True, text=True)
print("STDOUT:", p.stdout)
print("STDERR:", p.stderr)
'''

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
sftp = ssh.open_sftp()
with sftp.file('/tmp/apply_vt2_fix.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/apply_vt2_fix.py')
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
print('STDERR:\n', stderr.read().decode('utf-8', errors='ignore'))
ssh.close()


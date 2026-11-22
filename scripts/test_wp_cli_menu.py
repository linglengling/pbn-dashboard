import paramiko
import sys

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import subprocess

p1 = subprocess.run(["wp", "menu", "item", "add-custom", "67", "Brands", "#", "--porcelain", "--path=/www/wwwroot/j-core.biz", "--allow-root"], capture_output=True, text=True)
print("Added Brands ID:", p1.stdout.strip(), "Err:", p1.stderr.strip())
brands_id = p1.stdout.strip()

p2 = subprocess.run(["wp", "menu", "item", "add-custom", "67", "BU88", "https://bu88.com", f"--parent-id={brands_id}", "--path=/www/wwwroot/j-core.biz", "--allow-root"], capture_output=True, text=True)
print("Added BU88:", p2.stdout.strip())

p3 = subprocess.run(["wp", "menu", "item", "add-custom", "67", "VB88", "https://vb88.com", f"--parent-id={brands_id}", "--path=/www/wwwroot/j-core.biz", "--allow-root"], capture_output=True, text=True)
print("Added VB88:", p3.stdout.strip())
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)

sftp = ssh.open_sftp()
with sftp.file('/tmp/test_wp_cli_menu.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/test_wp_cli_menu.py')
sys.stdout.reconfigure(encoding='utf-8')
print("STDOUT:\n", stdout.read().decode('utf-8', errors='ignore'))
ssh.close()


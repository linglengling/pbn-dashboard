import paramiko
import json

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_script_lines = [
    "import subprocess, json",
    "",
    "sites = ['aaidudec.org', 'anthonyruivivar.net', 'bblatinamerica.com', 'sougicocoro.com']",
    "for s in sites:",
    "    print('=== SITE:', s, '===')",
    "    cmd = f'wp --allow-root --path=/www/wwwroot/{s} menu list --format=json'",
    "    p = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, text=True)",
    "    print('Menus:', p.stdout.strip())",
    "    cmd2 = f'wp --allow-root --path=/www/wwwroot/{s} menu location list --format=json'",
    "    p2 = subprocess.run(cmd2, shell=True, stdout=subprocess.PIPE, text=True)",
    "    print('Locations:', p2.stdout.strip())",
]

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
    
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/test_menu.py', 'w') as f:
        f.write("\n".join(remote_script_lines))
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command('python3 /tmp/test_menu.py')
    print(stdout.read().decode('utf-8'))
    print(stderr.read().decode('utf-8'))
    ssh.close()

if __name__ == "__main__":
    main()


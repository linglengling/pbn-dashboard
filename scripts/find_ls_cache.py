import paramiko

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = [
    "import subprocess",
    "domain = 'sburlrecdept.com'",
    "path = f'/www/wwwroot/{domain}'",
    "p = subprocess.run(f'find {path}/wp-content -maxdepth 2 -type d', shell=True, stdout=subprocess.PIPE, text=True)",
    "print('wp-content dirs in sburlrecdept.com:')",
    "print(p.stdout)",
    "p2 = subprocess.run('grep -rn storagePath /usr/local/lsws/conf/', shell=True, stdout=subprocess.PIPE, text=True)",
    "print('OLS cache storage path:')",
    "print(p2.stdout)"
]

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
    
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/find_ls_cache.py', 'w') as f:
        f.write("\n".join(remote_code))
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command('python3 /tmp/find_ls_cache.py')
    print(stdout.read().decode('utf-8'))
    print(stderr.read().decode('utf-8'))
    ssh.close()

if __name__ == "__main__":
    main()

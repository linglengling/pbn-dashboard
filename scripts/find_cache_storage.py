import paramiko

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = [
    "import subprocess",
    "p = subprocess.run(\"grep -rn 'storagePath' /usr/local/lsws/\", shell=True, stdout=subprocess.PIPE, text=True)",
    "print('storagePath in /usr/local/lsws/:', p.stdout)",
    "p2 = subprocess.run(\"find / -type d -name '*cache*' 2>/dev/null | grep -E 'lshttpd|lsws|panel'\", shell=True, stdout=subprocess.PIPE, text=True)",
    "print('cache dirs:', p2.stdout)"
]

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
    
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/find_cache_storage.py', 'w') as f:
        f.write("\n".join(remote_code))
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command('python3 /tmp/find_cache_storage.py')
    print(stdout.read().decode('utf-8'))
    ssh.close()

if __name__ == "__main__":
    main()


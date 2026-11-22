import paramiko

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = [
    "import subprocess",
    "p = subprocess.run(\"grep -inE 'cache|storage' /usr/local/lsws/conf/httpd_config.conf\", shell=True, stdout=subprocess.PIPE, text=True)",
    "print('Matches in httpd_config.conf:')",
    "print(p.stdout)",
    "p2 = subprocess.run(\"grep -inE 'cache' /usr/local/lsws/conf/vhosts/*/*.conf\", shell=True, stdout=subprocess.PIPE, text=True)",
    "print('Matches in vhost configs:')",
    "print(p2.stdout[:1000])"
]

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
    
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/find_cache_conf.py', 'w') as f:
        f.write("\n".join(remote_code))
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command('python3 /tmp/find_cache_conf.py')
    print(stdout.read().decode('utf-8'))
    ssh.close()

if __name__ == "__main__":
    main()


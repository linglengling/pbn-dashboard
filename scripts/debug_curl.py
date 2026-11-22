import paramiko

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = [
    "import subprocess",
    "cmd = \"curl -s -k -I -H 'Host: sburlrecdept.com' https://127.0.0.1/\"",
    "p = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, text=True)",
    "print('Headers:\\n', p.stdout)",
    "cmd2 = \"curl -s -k -H 'Host: sburlrecdept.com' https://127.0.0.1/ | head -n 30\"",
    "p2 = subprocess.run(cmd2, shell=True, stdout=subprocess.PIPE, text=True)",
    "print('Body start:\\n', p2.stdout)"
]

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
    
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/debug_curl.py', 'w') as f:
        f.write("\n".join(remote_code))
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command('python3 /tmp/debug_curl.py')
    print(stdout.read().decode('utf-8'))
    print(stderr.read().decode('utf-8'))
    ssh.close()

if __name__ == "__main__":
    main()


import paramiko

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import os, subprocess

cmd = "find /root /www/backup /tmp /home -maxdepth 4 -name '*.sql' -o -name '*.tar*' -o -name '*.zip' -o -name '*.gz' 2>/dev/null"
p = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, text=True)
for line in p.stdout.splitlines():
    if not line.startswith('/tmp/pbn_backups'):
        print(line)
"""

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
    
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/find_archives.py', 'w') as f:
        f.write(remote_code)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command('python3 /tmp/find_archives.py')
    print(stdout.read().decode('utf-8'))
    ssh.close()

if __name__ == "__main__":
    main()


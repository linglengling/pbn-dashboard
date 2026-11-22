import paramiko

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import subprocess
p = subprocess.run(['ps', 'aux'], stdout=subprocess.PIPE, text=True)
for line in p.stdout.splitlines():
    if 'litespeed' in line.lower() or 'lshttpd' in line.lower() or 'openlitespeed' in line.lower():
        print(line)

p2 = subprocess.run(['ls', '-ld', '/tmp/lshttpd'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
print(p2.stdout)
print(p2.stderr)
"""

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
    
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/check_cache.py', 'w') as f:
        f.write(remote_code)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command('python3 /tmp/check_cache.py')
    print(stdout.read().decode('utf-8'))
    print(stderr.read().decode('utf-8'))
    ssh.close()

if __name__ == "__main__":
    main()

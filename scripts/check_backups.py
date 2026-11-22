import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
    
    stdin, stdout, stderr = ssh.exec_command('ls -lh /tmp/pbn_backups/')
    print("BACKUPS:\n", stdout.read().decode('utf-8', errors='ignore'))
    ssh.close()

if __name__ == "__main__":
    main()


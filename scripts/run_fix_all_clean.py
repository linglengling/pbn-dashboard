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
    
    sftp = ssh.open_sftp()
    sftp.put("scripts/fix_all_sites_clean.py", "/tmp/fix_all_sites_clean.py")
    sftp.close()
    
    print("Running fix_all_sites_clean.py on VPS...")
    stdin, stdout, stderr = ssh.exec_command('python3 /tmp/fix_all_sites_clean.py')
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    print("OUTPUT:\n", out)
    if err:
        print("ERRORS:\n", err)
    ssh.close()

if __name__ == "__main__":
    main()


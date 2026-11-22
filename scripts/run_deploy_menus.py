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
    sftp.put("scripts/deploy_menus.py", "/tmp/deploy_menus.py")
    sftp.close()
    
    print("Executing deploy_menus.py on VPS...")
    stdin, stdout, stderr = ssh.exec_command('python3 /tmp/deploy_menus.py')
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    print("OUTPUT:\n", out)
    if err:
        print("ERRORS:\n", err)
        
    sftp = ssh.open_sftp()
    sftp.get("/tmp/menu_results.json", "menu_results.json")
    sftp.close()
    print("Downloaded menu_results.json")
    ssh.close()

if __name__ == "__main__":
    main()


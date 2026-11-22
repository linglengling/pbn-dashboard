import paramiko
import json
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
    sftp.get("/tmp/dead_links_audit.json", "dead_links_audit.json")
    sftp.close()
    ssh.close()
    print("Successfully downloaded dead_links_audit.json")

if __name__ == "__main__":
    main()


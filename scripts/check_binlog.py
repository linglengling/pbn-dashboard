import paramiko

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import subprocess

p = subprocess.run("mysql -uroot -pdc2fe6f2608cdc00 -N -e \\"SHOW VARIABLES LIKE 'log_bin'\\"", shell=True, stdout=subprocess.PIPE, text=True)
print("log_bin:", p.stdout)
p2 = subprocess.run("mysql -uroot -pdc2fe6f2608cdc00 -N -e \\"SHOW BINARY LOGS\\"", shell=True, stdout=subprocess.PIPE, text=True)
print("binary logs:", p2.stdout)
"""

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
    
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/check_binlog.py', 'w') as f:
        f.write(remote_code)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command('python3 /tmp/check_binlog.py')
    print(stdout.read().decode('utf-8'))
    ssh.close()

if __name__ == "__main__":
    main()


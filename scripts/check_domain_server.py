import paramiko

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import sqlite3

conn = sqlite3.connect('/www/wwwroot/phn-manage.sites/server/pbn_matrix.db')
cur = conn.cursor()
cur.execute("SELECT domain, server_id, server_host, server_ip FROM sites WHERE domain LIKE '%anthonyruivivar%' OR domain LIKE '%aaidudec%'")
for r in cur.fetchall():
    print(r)
conn.close()
"""

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
    
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/check_domain_server.py', 'w') as f:
        f.write(remote_code)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command('python3 /tmp/check_domain_server.py')
    print(stdout.read().decode('utf-8'))
    ssh.close()

if __name__ == "__main__":
    main()


import paramiko

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import sqlite3

conn = sqlite3.connect('/www/wwwroot/phn-manage.sites/server/pbn_matrix.db')
cur = conn.cursor()
cur.execute("SELECT id, name, host FROM servers WHERE host LIKE '%103.106.105.77%'")
print("Servers:", cur.fetchall())
cur.execute("SELECT count(*) FROM sites")
print("Total sites:", cur.fetchone()[0])
cur.execute("SELECT domain, server_id, server_host FROM sites LIMIT 10")
for r in cur.fetchall():
    print(r)
conn.close()
"""

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
    
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/check_sites_table.py', 'w') as f:
        f.write(remote_code)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command('python3 /tmp/check_sites_table.py')
    print(stdout.read().decode('utf-8'))
    ssh.close()

if __name__ == "__main__":
    main()


import paramiko

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = r'''
import os, subprocess, pymysql

print("=== SHOW DATABASES ===")
conn = pymysql.connect(host='127.0.0.1', user='root', password='dc2fe6f2608cdc00')
cur = conn.cursor()
cur.execute("SHOW DATABASES")
dbs = [r[0] for r in cur.fetchall()]
print("Total databases:", len(dbs))
for db in dbs:
    if 'backup' in db or 'bak' in db or 'old' in db or 'wp_' in db:
        print("DB:", db)

print("\n=== /www/backup/ database directory ===")
subprocess.run("ls -la /www/backup/database/", shell=True)

print("\n=== /www/server/data ===")
subprocess.run("ls -la /www/server/data/wp_aaidudec_org", shell=True)

print("\n=== /tmp/ dumps ===")
subprocess.run("ls -la /tmp/*.sql", shell=True)
'''

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
    
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/inspect_db_env.py', 'w') as f:
        f.write(remote_code)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command('python3 /tmp/inspect_db_env.py')
    print("STDOUT:", stdout.read().decode('utf-8'))
    print("STDERR:", stderr.read().decode('utf-8'))
    ssh.close()

if __name__ == "__main__":
    main()

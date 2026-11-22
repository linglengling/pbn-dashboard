import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import pymysql, subprocess

# 1. Restore aaidudec.org
subprocess.run("mysql -uroot -pdc2fe6f2608cdc00 wp_aaidudec_org < /tmp/pbn_backups/aaidudec.org_24.sql", shell=True)

# 2. Check via pymysql
conn = pymysql.connect(host='127.0.0.1', user='root', password='dc2fe6f2608cdc00', database='wp_aaidudec_org')
cur = conn.cursor()
cur.execute("SELECT post_content FROM wp_posts WHERE ID=24")
content = cur.fetchone()[0]
conn.close()

has_literal = ('\\\\n' in content)
has_real = ('\\n' in content)

print("Content length:", len(content))
print("Does it have literal backslash-n?", has_literal)
print("Does it have real newline?", has_real)
print("First 300 chars repr:")
print(repr(content[:300]))
"""

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
    
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/test_restore_one.py', 'w') as f:
        f.write(remote_code)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command('python3 /tmp/test_restore_one.py')
    print(stdout.read().decode('utf-8'))
    print(stderr.read().decode('utf-8'))
    ssh.close()

if __name__ == "__main__":
    main()

import paramiko

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import pymysql, json

conn = pymysql.connect(host="127.0.0.1", user="root", password="dc2fe6f2608cdc00", database="wp_kvdevelopers")
cur = conn.cursor()
cur.execute("SELECT meta_value FROM 9sapp_postmeta WHERE post_id=554 AND meta_key='_elementor_data'")
elem_tree = json.loads(cur.fetchone()[0])
print(json.dumps(elem_tree[-1], indent=2))
conn.close()
"""

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
    
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/print_last_elem.py', 'w') as f:
        f.write(remote_code)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command('python3 /tmp/print_last_elem.py')
    print(stdout.read().decode('utf-8'))
    ssh.close()

if __name__ == "__main__":
    main()


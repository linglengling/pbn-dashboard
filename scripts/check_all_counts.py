import paramiko
import json

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import json, pymysql

with open('/tmp/site_configs.json', 'r') as f:
    configs = json.load(f)

for c in configs:
    db = c['db_name']
    prefix = c['prefix']
    domain = c['domain']
    try:
        conn = pymysql.connect(host='127.0.0.1', user='root', password='dc2fe6f2608cdc00', database=db)
        cur = conn.cursor()
        cur.execute(f"SELECT count(*) FROM {prefix}posts")
        cnt = cur.fetchone()[0]
        cur.execute(f"SELECT count(*) FROM {prefix}posts WHERE post_type='nav_menu_item'")
        nav_cnt = cur.fetchone()[0]
        conn.close()
        print(f"{domain} ({db}): total_posts={cnt}, nav_menu_items={nav_cnt}")
    except Exception as e:
        print(f"{domain}: ERROR {e}")
"""

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
    
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/check_all_counts.py', 'w') as f:
        f.write(remote_code)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command('python3 /tmp/check_all_counts.py')
    print(stdout.read().decode('utf-8'))
    ssh.close()

if __name__ == "__main__":
    main()


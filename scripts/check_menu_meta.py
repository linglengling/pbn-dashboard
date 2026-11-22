import paramiko

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import pymysql

conn = pymysql.connect(host='127.0.0.1', user='root', password='dc2fe6f2608cdc00', database='wp_anthonyruiviv')
cur = conn.cursor()
pids = [2052, 2054, 2055, 2056, 2057, 2058, 2059, 2060, 2061, 2062, 2063, 2064, 2195]
cur.execute(f"SELECT post_id, meta_key, meta_value FROM wp_postmeta WHERE post_id IN ({','.join(map(str, pids))}) ORDER BY post_id, meta_key")
rows = cur.fetchall()
meta_by_id = {}
for pid, k, v in rows:
    if pid not in meta_by_id:
        meta_by_id[pid] = {}
    meta_by_id[pid][k] = v

for pid in pids:
    print(pid, meta_by_id.get(pid, {}))
conn.close()
"""

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
    
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/check_menu_meta.py', 'w') as f:
        f.write(remote_code)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command('python3 /tmp/check_menu_meta.py')
    print(stdout.read().decode('utf-8'))
    ssh.close()

if __name__ == "__main__":
    main()


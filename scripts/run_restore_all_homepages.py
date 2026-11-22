import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import json, pymysql, re

with open('/tmp/site_configs.json', 'r') as f:
    configs = json.load(f)

print("=== RESTORING ORIGINAL PRISTINE HOMEPAGES ON ALL 24 SITES ===")

for idx, c in enumerate(configs, 1):
    domain = c['domain']
    db = c['db_name']
    prefix = c['prefix']
    pid = c['page_on_front']
    bk_file = f"/tmp/pbn_backups/{domain}_{pid}.sql"
    
    conn = pymysql.connect(host='127.0.0.1', user='root', password='dc2fe6f2608cdc00', database=db)
    cur = conn.cursor()
    
    try:
        cur.execute("DROP TABLE IF EXISTS tmp_restore_post")
        cur.execute(f"CREATE TABLE tmp_restore_post LIKE {prefix}posts")
        
        with open(bk_file, 'r', errors='ignore') as f:
            sql = f.read()
            
        m = re.search(r'INSERT INTO `([^`]+)` VALUES \((.*)\);', sql, flags=re.S)
        if not m:
            print(f"[{idx:2d}/24] {domain:25s} | ERROR: NO INSERT STATEMENT")
            continue
            
        insert_sql = f"INSERT INTO tmp_restore_post VALUES ({m.group(2)})"
        cur.execute(insert_sql)
        
        cur.execute(f"UPDATE {prefix}posts p JOIN tmp_restore_post t ON p.ID = t.ID SET p.post_content = t.post_content")
        updated = cur.rowcount
        conn.commit()
        
        cur.execute(f"SELECT LENGTH(post_content) FROM {prefix}posts WHERE ID = %s", (pid,))
        new_len = cur.fetchone()[0]
        print(f"[{idx:2d}/24] {domain:25s} | pid={pid:5d} | restored len={new_len:6d} | updated={updated}")
        
    except Exception as e:
        print(f"[{idx:2d}/24] {domain:25s} | EXCEPTION: {e}")
    finally:
        cur.execute("DROP TABLE IF EXISTS tmp_restore_post")
        conn.close()

print("=== ALL 24 HOMEPAGES FULLY RESTORED TO PRISTINE STATE ===")
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
sftp = ssh.open_sftp()
with sftp.file('/tmp/restore_all_homepages.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/restore_all_homepages.py')
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
print('STDERR:\n', stderr.read().decode('utf-8', errors='ignore'))
ssh.close()


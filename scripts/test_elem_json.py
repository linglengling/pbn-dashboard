import paramiko

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import pymysql, json, re, subprocess

db = "wp_kvdevelopers"
prefix = "9sapp_"
pid = 554

conn = pymysql.connect(host="127.0.0.1", user="root", password="dc2fe6f2608cdc00", database=db)
cur = conn.cursor()

cur.execute(f"SELECT meta_value FROM {prefix}postmeta WHERE post_id={pid} AND meta_key='_elementor_data'")
row = cur.fetchone()
raw_data = row[0]
print(f"Loaded raw elementor data: {len(raw_data)} chars")

try:
    elem_tree = json.loads(raw_data)
    print("Successfully parsed with standard json.loads!")
except Exception as e:
    print("Error with raw_data:", e)
    # in WordPress, quotes or backslashes might be escaped with stripslashes
    import codecs
    cleaned = raw_data.encode().decode('unicode-escape')
    try:
        elem_tree = json.loads(cleaned)
        print("Successfully parsed after unicode-escape!")
    except Exception as e2:
        print("Error with unicode-escape:", e2)

conn.close()
"""

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
    
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/test_elem_json.py', 'w') as f:
        f.write(remote_code)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command('python3 /tmp/test_elem_json.py')
    print(stdout.read().decode('utf-8'))
    print(stderr.read().decode('utf-8'))
    ssh.close()

if __name__ == "__main__":
    main()


import paramiko

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import sqlite3

conn = sqlite3.connect('/www/wwwroot/pbn-management2.keodinh.net/pbn_matrix.db')
cur = conn.cursor()
domains = [
    'aaidudec.org', 'anthonyruivivar.net', 'bblatinamerica.com', 'conadecivil.com',
    'facturatabasco.com', 'greatdrivingchallenge.com', 'hkhoe.com', 'sburlrecdept.com',
    'shadowdance.org', 'smvhighschool.in', 'snow-design.com', 'stepl.org',
    'suzanneloebl.com', 'thaiasiatoday.com', 'feshun.com', 'hellbenderpress.com',
    'innkeeperrockies.com', 'rogalevich.org', 'j-core.biz', 'kvdevelopers.com',
    'benscarpage.com', 'kylehendersonmusic.com', 'respectablyfrench.com', 'sougicocoro.com'
]

cur.execute("PRAGMA table_info(sites)")
print("Cols:", [c[1] for c in cur.fetchall()])

for d in domains:
    cur.execute("SELECT domain, server_id, site_url, total_homepage_links FROM sites WHERE domain LIKE ?", (f"%{d}%",))
    print(d, cur.fetchall())
conn.close()
"""

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
    
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/check_pbn2_sites.py', 'w') as f:
        f.write(remote_code)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command('python3 /tmp/check_pbn2_sites.py')
    print(stdout.read().decode('utf-8'))
    ssh.close()

if __name__ == "__main__":
    main()


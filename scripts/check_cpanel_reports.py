import sqlite3
import paramiko

conn = sqlite3.connect('PBN-Dashboard-V2/pbn_matrix.db')
cur = conn.cursor()
cur.execute("SELECT name, host, username, password FROM servers WHERE type = 'cpanel'")
servers = cur.fetchall()
conn.close()

for srv in servers:
    name, host, user, pwd = srv
    print(f"=== SERVER: {name} ({host}) ===")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=user, password=pwd, timeout=15)
        stdin, stdout, stderr = ssh.exec_command("ls -lh ~/pbn-tool/wp_report_cpanel_*.csv | tail -n 1 ; wc -l ~/pbn-tool/wp_report_cpanel_*.csv | tail -n 1")
        print(stdout.read().decode())
        ssh.close()
    except Exception as e:
        print("Error:", e)


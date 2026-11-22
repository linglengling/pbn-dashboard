import sqlite3, paramiko

conn = sqlite3.connect('PBN-Dashboard-V2/pbn_matrix.db')
servers = conn.execute("SELECT name, host, username, password FROM servers WHERE type = 'cpanel'").fetchall()
conn.close()

for srv in servers:
    name, host, user, pwd = srv
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=pwd, timeout=15)
    stdin, stdout, stderr = ssh.exec_command("head -n 4 ~/pbn-tool/wp_report_cpanel_*.csv")
    print(f"=== {name} Sample Sites ===")
    print(stdout.read().decode())
    ssh.close()


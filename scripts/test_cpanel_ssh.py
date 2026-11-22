import sqlite3
import paramiko

conn = sqlite3.connect('PBN-Dashboard-V2/pbn_matrix.db')
cur = conn.cursor()
cur.execute("SELECT id, name, type, host, username, password FROM servers WHERE type = 'cpanel' LIMIT 1")
srv = cur.fetchone()
conn.close()

if srv:
    print(f"Connecting to {srv[1]} ({srv[3]}) as {srv[4]}...")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(srv[3], username=srv[4], password=srv[5], timeout=10)
        
        stdin, stdout, stderr = ssh.exec_command("whoami ; pwd ; ls -la ; which chattr ; which wp ; which php")
        print("=== SSH TEST ===")
        print(stdout.read().decode())
        
        stdin, stdout, stderr = ssh.exec_command("find ~/public_html ~/domains -maxdepth 3 -name 'wp-config.php' 2>/dev/null")
        print("=== WP SITES FOUND ===")
        print(stdout.read().decode())
        
        ssh.close()
    except Exception as e:
        print("SSH Connection Error:", e)


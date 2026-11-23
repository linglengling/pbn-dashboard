import paramiko

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("103.106.105.77", username="root", password="q9icdLH1!*0B", timeout=20)
    
    script = """
import sqlite3

def dump_db(path):
    print(f"=== DB: {path} ===")
    try:
        conn = sqlite3.connect(path)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in c.fetchall()]
        print("Tables:", tables)
        for t in tables:
            try:
                c.execute(f"SELECT * FROM {t} ORDER BY rowid DESC LIMIT 3")
                print(f"Table {t} sample:", c.fetchall())
            except Exception as e:
                print(f"Error {t}: {e}")
        conn.close()
    except Exception as e:
        print("Error:", e)

dump_db('/www/server/mausbot/data/messages.db')
dump_db('/www/server/mausbot/data/runtime.db')
"""
    sftp = ssh.open_sftp()
    with sftp.open('/tmp/dump_mausbot_dbs.py', 'w') as f:
        f.write(script)
    sftp.close()

    stdin, stdout, stderr = ssh.exec_command("python3 /tmp/dump_mausbot_dbs.py")
    print(stdout.read().decode())
    ssh.close()

if __name__ == "__main__":
    main()

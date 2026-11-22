import paramiko

servers = [
    {'name': 'VPS 1 (194.233.83.83)', 'host': '194.233.83.83', 'user': 'root', 'pass': 'E^@r8&R6~NFo/!'},
    {'name': 'VPS 2 (172.96.190.231)', 'host': '172.96.190.231', 'user': 'root', 'pass': 'BkUEwvB9QavrrfEmfbah'},
    {'name': 'VPS 3 (198.252.110.104)', 'host': '198.252.110.104', 'user': 'root', 'pass': 'kzIM1OysATQMdi9MogDd'},
    {'name': 'VPS 4 (198.252.101.160)', 'host': '198.252.101.160', 'user': 'root', 'pass': 'pi6W0HbBOJjqcYL1Q3Yn'},
    {'name': 'VPS 5 (198.252.99.79)', 'host': '198.252.99.79', 'user': 'root', 'pass': 'rv0xH9UazYoUFfgwu3bC'},
    {'name': 'VPS 6 (172.96.184.18)', 'host': '172.96.184.18', 'user': 'root', 'pass': '4tRfQAXR3Zt1vzspvMRy'},
    {'name': 'VPS 7 (154.26.129.207)', 'host': '154.26.129.207', 'user': 'root', 'pass': '9W35EwykgwT~tygw'}
]

for s in servers:
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(s['host'], port=22, username=s['user'], password=s['pass'], timeout=6)
        cmd = "find /www/backup -name '*.sql*' 2>/dev/null | head -n 30"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        out = stdout.read().decode('utf-8').strip()
        print(f"=== {s['name']} ===")
        print(out if out else "(none)")
        ssh.close()
    except Exception as e:
        print(f"=== {s['name']} === ERROR: {e}")


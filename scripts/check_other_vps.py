import paramiko

servers = [
    {'name': 'VPS aaPanel 1', 'host': '194.233.83.83', 'user': 'root', 'pass': 'E^@r8&R6~NFo/!'},
    {'name': 'VPS aaPanel 2', 'host': '172.96.190.231', 'user': 'root', 'pass': 'BkUEwvB9QavrrfEmfbah'},
    {'name': 'VPS aaPanel 3', 'host': '198.252.110.104', 'user': 'root', 'pass': 'kzIM1OysATQMdi9MogDd'},
    {'name': 'VPS aaPanel 4', 'host': '198.252.101.160', 'user': 'root', 'pass': 'pi6W0HbBOJjqcYL1Q3Yn'},
    {'name': 'VPS aaPanel 5', 'host': '198.252.99.79', 'user': 'root', 'pass': 'rv0xH9UazYoUFfgwu3bC'},
    {'name': 'VPS aaPanel 6', 'host': '172.96.184.18', 'user': 'root', 'pass': '4tRfQAXR3Zt1vzspvMRy'},
    {'name': 'VPS aaPanel 7', 'host': '154.26.129.207', 'user': 'root', 'pass': '9W35EwykgwT~tygw'}
]

for s in servers:
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(s['host'], port=22, username=s['user'], password=s['pass'], timeout=5)
        stdin, stdout, stderr = ssh.exec_command("find /www/backup -name '*anthony*' -o -name '*aaidudec*' 2>/dev/null; ls /www/wwwroot/ | grep -E 'anthony|aaidudec'")
        out = stdout.read().decode('utf-8').strip()
        print(f"=== {s['name']} ({s['host']}) ===")
        print(out if out else "(none)")
        ssh.close()
    except Exception as e:
        print(f"=== {s['name']} ({s['host']}) === ERROR: {e}")


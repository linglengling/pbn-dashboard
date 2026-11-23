import paramiko
import time

def connect_ssh():
    for attempt in range(3):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect("103.106.105.77", username="root", password="q9icdLH1!*0B", timeout=20)
            return ssh
        except Exception as e:
            print(f"SSH attempt {attempt+1} failed: {e}")
            time.sleep(2)
    raise RuntimeError("SSH connection failed after 3 attempts")

def main():
    ssh = connect_ssh()
    
    script = """
listen_80 = "/www/server/panel/vhost/openlitespeed/listen/80.conf"
with open(listen_80, "r") as f:
    content = f.read()

lines = [l for l in content.splitlines() if not l.strip().startswith("map\tteam.kiencanh.com") and not l.strip().startswith("map team.kiencanh.com")]
cleaned = "\\n".join(lines)

target = "map default *"
if target in cleaned:
    idx = cleaned.find(target)
    new_content = cleaned[:idx] + "\\tmap\\tteam.kiencanh.com team.kiencanh.com\\n    " + cleaned[idx:]
    with open(listen_80, "w") as f:
        f.write(new_content)
    print("Fixed listen/80.conf placement.")

import os
os.system("/usr/local/lsws/bin/lswsctrl reload")
"""
    sftp = ssh.open_sftp()
    with sftp.open('/tmp/fix_listen80.py', 'w') as f:
        f.write(script)
    sftp.close()

    stdin, stdout, stderr = ssh.exec_command("python3 /tmp/fix_listen80.py")
    print(stdout.read().decode())
    
    time.sleep(1)

    stdin, stdout, stderr = ssh.exec_command("curl -s -i -H 'Host: team.kiencanh.com' http://127.0.0.1:80/pair")
    print("NEW 80 PAIR:\n", stdout.read().decode()[:400])

    stdin, stdout, stderr = ssh.exec_command("curl -s -k -i -H 'Host: team.kiencanh.com' https://127.0.0.1:443/pair")
    print("NEW 443 PAIR:\n", stdout.read().decode()[:400])

    ssh.close()

if __name__ == "__main__":
    main()

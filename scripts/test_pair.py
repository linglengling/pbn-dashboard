import paramiko

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("103.106.105.77", username="root", password="q9icdLH1!*0B", timeout=20)
    
    stdin, stdout, stderr = ssh.exec_command("cat /www/server/panel/vhost/openlitespeed/listen/80.conf | grep team")
    print("LISTEN 80:\n", stdout.read().decode())

    stdin, stdout, stderr = ssh.exec_command("curl -s -k -i -H 'Host: team.kiencanh.com' https://127.0.0.1:443/pair")
    print("443 PAIR:\n", stdout.read().decode()[:400])

    stdin, stdout, stderr = ssh.exec_command("curl -s -i -H 'Host: team.kiencanh.com' http://127.0.0.1:80/pair")
    print("80 PAIR:\n", stdout.read().decode()[:400])

    ssh.close()

if __name__ == "__main__":
    main()

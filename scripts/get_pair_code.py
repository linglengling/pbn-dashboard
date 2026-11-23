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
            time.sleep(2)
    raise RuntimeError("SSH failed")

def main():
    ssh = connect_ssh()

    # Kiem tra account status
    stdin, stdout, stderr = ssh.exec_command("openmausbot account status --data-dir /www/server/mausbot/data")
    print("ACCOUNT STATUS:\n", stdout.read().decode())

    # Tao pairing code moi voi TTL 24h
    stdin, stdout, stderr = ssh.exec_command("openmausbot pair --data-dir /www/server/mausbot/data --ttl 24h")
    pair_output = stdout.read().decode()
    print("PAIR OUTPUT:\n", pair_output)

    # Kiem tra pm2 status
    stdin, stdout, stderr = ssh.exec_command("pm2 status mausbot")
    print("PM2 STATUS:\n", stdout.read().decode())

    ssh.close()

if __name__ == "__main__":
    main()

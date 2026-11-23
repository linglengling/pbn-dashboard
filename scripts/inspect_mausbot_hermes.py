import paramiko

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("103.106.105.77", username="root", password="q9icdLH1!*0B", timeout=20)
    
    cmd = "ls -la /www/server/mausbot/data/providers"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print("PROVIDERS:\n", stdout.read().decode())

    cmd2 = "tail -n 30 /root/.pm2/logs/mausbot-out.log"
    stdin, stdout, stderr = ssh.exec_command(cmd2)
    print("PM2 OUT LOGS:\n", stdout.read().decode())

    cmd3 = "tail -n 30 /root/.pm2/logs/mausbot-error.log"
    stdin, stdout, stderr = ssh.exec_command(cmd3)
    print("PM2 ERR LOGS:\n", stdout.read().decode())

    ssh.close()

if __name__ == "__main__":
    main()

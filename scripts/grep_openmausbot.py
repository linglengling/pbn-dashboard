import paramiko

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("103.106.105.77", username="root", password="q9icdLH1!*0B", timeout=20)
    
    cmd = 'grep -rn "hermesAgent" /www/server/nodejs/v25.9.0/lib/node_modules/openmausbot/'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print("GREP:\n", stdout.read().decode())

    ssh.close()

if __name__ == "__main__":
    main()

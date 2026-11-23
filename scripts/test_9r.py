import paramiko

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("103.106.105.77", username="root", password="q9icdLH1!*0B", timeout=20)
    
    script = """
import urllib.request, json

data = json.dumps({
    "model": "9router-1",
    "messages": [{"role": "user", "content": "ping"}]
}).encode()

req = urllib.request.Request(
    "http://127.0.0.1:20128/v1/chat/completions",
    data=data,
    headers={"Content-Type": "application/json", "Authorization": "Bearer sk-9router"}
)
try:
    with urllib.request.urlopen(req, timeout=10) as r:
        print("9Router Response:", r.read().decode()[:300])
except Exception as e:
    print("9Router Error:", e)
"""
    sftp = ssh.open_sftp()
    with sftp.open('/tmp/test_9router.py', 'w') as f:
        f.write(script)
    sftp.close()

    stdin, stdout, stderr = ssh.exec_command("python3 /tmp/test_9router.py")
    print(stdout.read().decode())
    ssh.close()

if __name__ == "__main__":
    main()

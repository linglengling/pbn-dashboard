import paramiko

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("103.106.105.77", username="root", password="q9icdLH1!*0B", timeout=20)
    
    script = """
import yaml

with open('/root/.hermes/config.yaml', 'r') as f:
    cfg = yaml.safe_load(f)

cfg['model']['default'] = '9router-1'
cfg['model']['provider'] = 'custom'
cfg['model']['base_url'] = 'http://127.0.0.1:20128/v1'
cfg['model']['api_key'] = 'sk-5e56e0df71e579e4-ub03ec-ca217f91'

with open('/root/.hermes/config.yaml', 'w') as f:
    yaml.safe_dump(cfg, f, default_flow_style=False)

print("Updated config.yaml with custom provider!")
"""
    sftp = ssh.open_sftp()
    with sftp.open('/tmp/test_update_hermes2.py', 'w') as f:
        f.write(script)
    sftp.close()

    stdin, stdout, stderr = ssh.exec_command("python3 /tmp/test_update_hermes2.py")
    print(stdout.read().decode())
    
    stdin, stdout, stderr = ssh.exec_command("hermes -z 'reply with only PONG' chat")
    print("CHAT RESPONSE:\n", stdout.read().decode())
    print("CHAT ERR:\n", stderr.read().decode())
    ssh.close()

if __name__ == "__main__":
    main()

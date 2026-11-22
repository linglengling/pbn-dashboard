import paramiko
import json

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = [
    "import subprocess, json",
    "p = subprocess.run(['mysql', '-uroot', '-pdc2fe6f2608cdc00', 'wp_kvdevelopers', '-N', '-s', '-e', 'SELECT meta_value FROM 9sapp_postmeta WHERE post_id=554 AND meta_key=\"_elementor_data\"'], stdout=subprocess.PIPE, text=True)",
    "data = json.loads(p.stdout)",
    "print('Type of data:', type(data))",
    "print('Number of root sections:', len(data))",
    "print('Keys of last section:', list(data[-1].keys()))",
    "print('Last section widget type:', data[-1].get('elements', [{}])[0].get('elements', [{}])[0].get('widgetType'))",
]

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
    
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/inspect_elem.py', 'w') as f:
        f.write("\n".join(remote_code))
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command('python3 /tmp/inspect_elem.py')
    print(stdout.read().decode('utf-8'))
    ssh.close()

if __name__ == "__main__":
    main()


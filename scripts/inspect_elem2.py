import paramiko

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = [
    "import subprocess",
    "p = subprocess.run(['mysql', '-uroot', '-pdc2fe6f2608cdc00', 'wp_kvdevelopers', '-N', '-s', '-e', 'SELECT LENGTH(meta_value) FROM 9sapp_postmeta WHERE post_id=554 AND meta_key=\"_elementor_data\"'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)",
    "print('Length:', p.stdout, p.stderr)",
    "p2 = subprocess.run(['mysql', '-uroot', '-pdc2fe6f2608cdc00', 'wp_kvdevelopers', '-N', '-s', '-e', 'SELECT LEFT(meta_value, 200) FROM 9sapp_postmeta WHERE post_id=554 AND meta_key=\"_elementor_data\"'], stdout=subprocess.PIPE, text=True)",
    "print('Left 200:', p2.stdout)"
]

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
    
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/inspect_elem2.py', 'w') as f:
        f.write("\n".join(remote_code))
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command('python3 /tmp/inspect_elem2.py')
    print(stdout.read().decode('utf-8'))
    print(stderr.read().decode('utf-8'))
    ssh.close()

if __name__ == "__main__":
    main()


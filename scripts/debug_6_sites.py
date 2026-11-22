import paramiko
import json

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import json, subprocess

sites_to_check = [
    'sburlrecdept.com',
    'snow-design.com',
    'rogalevich.org',
    'kvdevelopers.com',
    'kylehendersonmusic.com',
    'sougicocoro.com'
]

with open('/tmp/site_configs.json', 'r') as f:
    configs = {c['domain']: c for c in json.load(f)}

for s in sites_to_check:
    c = configs[s]
    db = c['db_name']
    prefix = c['prefix']
    pid = c['page_on_front']
    
    # 1. Check if partner-network-section is in the DB
    cmd = ['mysql', '-uroot', '-pdc2fe6f2608cdc00', db, '-N', '-s', '-e',
           f\"SELECT post_content LIKE '%partner-network-section%' FROM {prefix}posts WHERE ID={pid}\"]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
    in_db = p.stdout.strip()
    
    # 2. Check curl locally on 127.0.0.1 to bypass Cloudflare
    cmd2 = f"curl -s -k -H 'Host: {s}' https://127.0.0.1 | grep -i 'partner-network-section'"
    p2 = subprocess.run(cmd2, shell=True, stdout=subprocess.PIPE, text=True)
    in_local = bool(p2.stdout.strip())
    
    # 3. Check what cache plugins are active
    cmd3 = f"wp --allow-root --path=/www/wwwroot/{s} plugin list --status=active --format=json"
    p3 = subprocess.run(cmd3, shell=True, stdout=subprocess.PIPE, text=True)
    try:
        plugins = [pl['name'] for pl in json.loads(p3.stdout)]
    except Exception:
        plugins = []
        
    print(f"Domain: {s} | In DB: {in_db} | In Local Curl: {in_local} | Plugins: {plugins}")
"""

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
    
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/debug_6_sites.py', 'w') as f:
        f.write(remote_code)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command('python3 /tmp/debug_6_sites.py')
    print(stdout.read().decode('utf-8'))
    print(stderr.read().decode('utf-8'))
    ssh.close()

if __name__ == "__main__":
    main()


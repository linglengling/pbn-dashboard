import paramiko
import sys

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import subprocess, json

targets = [
    (8, 'sburlrecdept.com', [('X8 Club', 'https://x8.club'), ('HD88', 'https://hd88.com')]),
    (9, 'shadowdance.org', [('BU88', 'https://bu88.com'), ('VB88', 'https://vb88.com')]),
    (10, 'smvhighschool.in', [('X8 Club', 'https://x8.club'), ('HD88', 'https://hd88.com')]),
    (11, 'snow-design.com', [('BU88', 'https://bu88.com'), ('VB88', 'https://vb88.com')]),
    (18, 'rogalevich.org', [('X8 Club', 'https://x8.club'), ('HD88', 'https://hd88.com')]),
    (20, 'kvdevelopers.com', [('X8 Club', 'https://x8.club'), ('HD88', 'https://hd88.com')]),
]

for idx, domain, brands in targets:
    path = f"/www/wwwroot/{domain}"
    
    # 1. Get primary menu term_id
    p = subprocess.run(["wp", "menu", "list", f"--path={path}", "--format=json", "--allow-root"], capture_output=True, text=True)
    if p.returncode != 0 or not p.stdout.strip():
        print(f"{domain}: Error listing menus: {p.stderr}")
        continue
    menus = json.loads(p.stdout)
    
    # Find menu with 'primary' or highest count
    target_menu_id = None
    for m in menus:
        locs = m.get('locations', [])
        if any('primary' in l for l in locs):
            target_menu_id = m['term_id']
            break
    if not target_menu_id and menus:
        target_menu_id = menus[0]['term_id']
        
    print(f"{domain}: target_menu_id = {target_menu_id}")
    
    # Add Brands
    p_b = subprocess.run(["wp", "menu", "item", "add-custom", str(target_menu_id), "Brands", "#", "--porcelain", f"--path={path}", "--allow-root"], capture_output=True, text=True)
    b_id = p_b.stdout.strip()
    print(f"  Added Brands ID={b_id}")
    
    for b_title, b_url in brands:
        p_c = subprocess.run(["wp", "menu", "item", "add-custom", str(target_menu_id), b_title, b_url, f"--parent-id={b_id}", f"--path={path}", "--allow-root"], capture_output=True, text=True)
        print(f"    Added {b_title} -> {p_c.stdout.strip()}")

subprocess.run("rm -rf /usr/local/lsws/cachedata/priv/*", shell=True)
subprocess.run("/usr/local/lsws/bin/lswsctrl reload", shell=True)
print("LSWS cache cleared and reloaded.")
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)

sftp = ssh.open_sftp()
with sftp.file('/tmp/add_brands_wpcli.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/add_brands_wpcli.py')
sys.stdout.reconfigure(encoding='utf-8')
print("STDOUT:\n", stdout.read().decode('utf-8', errors='ignore'))
print("STDERR:\n", stderr.read().decode('utf-8', errors='ignore'))
ssh.close()


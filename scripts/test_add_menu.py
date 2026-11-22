import paramiko
import sys

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = '''
import subprocess, json

domain = "aaidudec.org"
path = f"/www/wwwroot/{domain}"

# 1. Get menus
p = subprocess.run(f"wp --allow-root --path={path} menu list --format=json", shell=True, stdout=subprocess.PIPE, text=True)
menus = json.loads(p.stdout)
primary_menu = None
for m in menus:
    if any("primary" in loc for loc in m.get("locations", [])):
        primary_menu = m
        break
if not primary_menu and menus:
    primary_menu = menus[0]

print("Selected menu:", primary_menu)
menu_id = primary_menu["term_id"]

# 2. Check existing items
p_items = subprocess.run(f"wp --allow-root --path={path} menu item list {menu_id} --format=json", shell=True, stdout=subprocess.PIPE, text=True)
items = json.loads(p_items.stdout)
brand_parent = None
for it in items:
    if it.get("title") == "Brands":
        brand_parent = it
        break

if not brand_parent:
    print("Creating parent 'Brands'...")
    res = subprocess.run(f"wp --allow-root --path={path} menu item add-custom {menu_id} Brands '#' --porcelain", shell=True, stdout=subprocess.PIPE, text=True)
    parent_id = res.stdout.strip()
    print("Parent ID created:", parent_id)
else:
    parent_id = brand_parent["db_id"]
    print("Found existing Brands parent ID:", parent_id)

# 3. Add children: BU88 and VB88
# Check if child already exists
children = [it.get("title") for it in items if str(it.get("menu_item_parent")) == str(parent_id)]
print("Existing children under Brands:", children)

if "BU88" not in children:
    subprocess.run(f"wp --allow-root --path={path} menu item add-custom {menu_id} 'BU88' 'https://bu88.com' --parent-id={parent_id}", shell=True)
    print("Added BU88")

if "VB88" not in children:
    subprocess.run(f"wp --allow-root --path={path} menu item add-custom {menu_id} 'VB88' 'https://vb88.com' --parent-id={parent_id}", shell=True)
    print("Added VB88")

# 4. Verify menu items again
p_items2 = subprocess.run(f"wp --allow-root --path={path} menu item list {menu_id} --format=json", shell=True, stdout=subprocess.PIPE, text=True)
print("Updated menu items:")
for it in json.loads(p_items2.stdout):
    if it.get("title") in ("Brands", "BU88", "VB88"):
        print(f" - {it.get('db_id')} | {it.get('title')} | parent={it.get('menu_item_parent')} | url={it.get('url')}")
'''

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
    
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/test_add_menu.py', 'w') as f:
        f.write(remote_code)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command('python3 /tmp/test_add_menu.py')
    print(stdout.read().decode('utf-8'))
    print(stderr.read().decode('utf-8'))
    ssh.close()

if __name__ == "__main__":
    main()


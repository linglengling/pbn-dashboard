import json
import subprocess
import os
import sys

# Mapped exact active menu IDs
SITE_MENU_MAP = {
    "aaidudec.org": 6,
    "anthonyruivivar.net": 180,
    "bblatinamerica.com": 9,
    "conadecivil.com": 3,
    "facturatabasco.com": 2,
    "greatdrivingchallenge.com": 21,
    "hkhoe.com": 4,
    "sburlrecdept.com": 2,
    "shadowdance.org": 2,
    "smvhighschool.in": 67,
    "snow-design.com": 3,
    "stepl.org": 3,
    "suzanneloebl.com": 2,
    "thaiasiatoday.com": 5,
    "feshun.com": 2,
    "hellbenderpress.com": 6,
    "innkeeperrockies.com": 3,
    "rogalevich.org": 9,
    "j-core.biz": 67,
    "kvdevelopers.com": 2,
    "benscarpage.com": 2,
    "kylehendersonmusic.com": 4,
    "respectablyfrench.com": 2,
    "sougicocoro.com": 4,
}

with open('/tmp/site_configs.json', 'r') as f:
    configs = json.load(f)

print(f"Deploying 'Brands' dropdown menu across {len(configs)} sites...")

for idx, c in enumerate(configs, start=1):
    domain = c['domain']
    path = f"/www/wwwroot/{domain}"
    menu_id = SITE_MENU_MAP[domain]
    
    is_odd = (idx % 2 != 0)
    brands = [
        ("BU88", "https://bu88.com"),
        ("VB88", "https://vb88.com")
    ] if is_odd else [
        ("X8 Club", "https://x8.club"),
        ("HD88", "https://hd88.com")
    ]
    
    print(f"[{idx:02d}/24] {domain:26s} (Menu ID: {menu_id}, Group: {'ODD' if is_odd else 'EVEN'})...")
    
    # 1. Check existing items in this menu
    p = subprocess.run(
        ["wp", "menu", "item", "list", str(menu_id), f"--path={path}", "--format=json", "--allow-root"],
        capture_output=True, text=True
    )
    try:
        items = json.loads(p.stdout)
    except Exception:
        items = []
        
    # Check if Brands already exists
    parent_id = None
    for it in items:
        if it.get('title') == 'Brands':
            parent_id = it.get('db_id')
            break
            
    if not parent_id:
        p_b = subprocess.run(
            ["wp", "menu", "item", "add-custom", str(menu_id), "Brands", "#", "--porcelain", f"--path={path}", "--allow-root"],
            capture_output=True, text=True
        )
        parent_id = p_b.stdout.strip()
        print(f"  -> Created 'Brands' item (ID: {parent_id})")
    else:
        print(f"  -> 'Brands' item already exists (ID: {parent_id})")
        
    # 2. Add children under Brands
    existing_titles = [it.get('title') for it in items]
    for b_title, b_url in brands:
        if b_title not in existing_titles:
            p_c = subprocess.run(
                ["wp", "menu", "item", "add-custom", str(menu_id), b_title, b_url, f"--parent-id={parent_id}", "--target=_blank", "--porcelain", f"--path={path}", "--allow-root"],
                capture_output=True, text=True
            )
            print(f"  -> Added child '{b_title}' (ID: {p_c.stdout.strip()})")
        else:
            print(f"  -> Child '{b_title}' already exists")
            
    # Clean cache for this site
    if os.path.exists(f"{path}/wp-content/cache"):
        subprocess.run(f"rm -rf {path}/wp-content/cache/*", shell=True)

# Purge LSWS
subprocess.run("rm -rf /usr/local/lsws/cachedata/priv/*", shell=True)
subprocess.run("/usr/local/lsws/bin/lswsctrl restart", shell=True)
print("\nAll 24 sites Brands menu deployed and web server reloaded!")


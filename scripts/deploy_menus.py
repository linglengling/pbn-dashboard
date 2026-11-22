import os
import json
import subprocess

with open('/tmp/site_configs.json', 'r') as f:
    configs = json.load(f)

menu_assignments = {}
# Odd sites (1, 3, 5, 7, ... -> idx 0, 2, 4, 6, ...)
# BU88 (https://bu88.com) & VB88 (https://vb88.com)
# Even sites (2, 4, 6, 8, ... -> idx 1, 3, 5, 7, ...)
# X8 Club (https://x8.club) & HD88 (https://hd88.com)

results = []

for idx, c in enumerate(configs, start=1):
    domain = c['domain']
    path = f"/www/wwwroot/{domain}"
    is_odd = (idx % 2 != 0)
    
    brand_sublinks = [
        ("BU88", "https://bu88.com"),
        ("VB88", "https://vb88.com")
    ] if is_odd else [
        ("X8 Club", "https://x8.club"),
        ("HD88", "https://hd88.com")
    ]
    
    print(f"[{idx}/24] Processing Menu for {domain} (Group: {'ODD' if is_odd else 'EVEN'})...")
    
    # 1. Get menus
    p = subprocess.run(f"wp --allow-root --path={path} menu list --format=json", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        menus = json.loads(p.stdout)
    except Exception as e:
        print(f"  Error reading menus: {e}")
        results.append({'domain': domain, 'status': 'failed', 'error': str(e)})
        continue
        
    primary_menu = None
    for m in menus:
        locs = m.get('locations', [])
        if any('primary' in loc or 'main' in loc or 'header' in loc for loc in locs):
            primary_menu = m
            break
    if not primary_menu and menus:
        # fallback to the menu with highest count or first menu
        menus.sort(key=lambda x: x.get('count', 0), reverse=True)
        primary_menu = menus[0]
        
    if not primary_menu:
        # create a menu
        p_create = subprocess.run(f"wp --allow-root --path={path} menu create 'Main Menu' --porcelain", shell=True, stdout=subprocess.PIPE, text=True)
        menu_id = p_create.stdout.strip()
        # assign to primary location if available
        subprocess.run(f"wp --allow-root --path={path} menu location assign {menu_id} primary", shell=True)
        primary_menu = {'term_id': menu_id, 'name': 'Main Menu'}
        
    menu_id = primary_menu['term_id']
    print(f"  Using menu {menu_id} ('{primary_menu.get('name')}')")
    
    # 2. Check existing menu items
    p_items = subprocess.run(f"wp --allow-root --path={path} menu item list {menu_id} --format=json", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        items = json.loads(p_items.stdout)
    except Exception:
        items = []
        
    parent_id = None
    for it in items:
        if it.get('title') == 'Brands':
            parent_id = it.get('db_id')
            break
            
    if not parent_id:
        p_parent = subprocess.run(f"wp --allow-root --path={path} menu item add-custom {menu_id} 'Brands' '#' --porcelain", shell=True, stdout=subprocess.PIPE, text=True)
        parent_id = p_parent.stdout.strip()
        print(f"  Created Brands parent ID: {parent_id}")
    else:
        print(f"  Found existing Brands parent ID: {parent_id}")
        
    # 3. Add child items
    existing_titles = [it.get('title') for it in items]
    added_children = []
    for title, url in brand_sublinks:
        if title not in existing_titles:
            cmd_add = f"wp --allow-root --path={path} menu item add-custom {menu_id} '{title}' '{url}' --parent-id={parent_id}"
            subprocess.run(cmd_add, shell=True, stdout=subprocess.PIPE, text=True)
            added_children.append(title)
            print(f"  Added child: {title} ({url})")
        else:
            print(f"  Child already exists: {title}")
            
    results.append({
        'domain': domain,
        'menu_id': menu_id,
        'parent_id': parent_id,
        'brands': [t for t, u in brand_sublinks],
        'status': 'success'
    })

with open('/tmp/menu_results.json', 'w') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print("All menus processed successfully!")


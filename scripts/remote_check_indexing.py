import json
import pymysql
import os
import urllib.request
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

with open('/tmp/sites.json', 'r') as f:
    configs = json.load(f)

db = pymysql.connect(host='127.0.0.1', user='root', password='dc2fe6f2608cdc00')
cursor = db.cursor()

results = []

for idx, c in enumerate(configs, 1):
    domain = c['domain']
    db_name = c['db_name']
    prefix = c['prefix']
    
    # 1. Check blog_public in DB
    blog_public = None
    try:
        cursor.execute(f"SELECT option_value FROM `{db_name}`.`{prefix}options` WHERE option_name = 'blog_public'")
        row = cursor.fetchone()
        if row:
            blog_public = row[0]
    except Exception as e:
        blog_public = f"ERR: {e}"
        
    # 2. Check physical robots.txt in docroot
    docroot = f"/www/wwwroot/{domain}"
    robots_path = os.path.join(docroot, "robots.txt")
    has_physical_robots = os.path.exists(robots_path)
    robots_content = ""
    if has_physical_robots:
        try:
            with open(robots_path, 'r', errors='ignore') as rf:
                robots_content = rf.read().strip()
        except:
            pass

    # 3. Check live HTTP for meta robots & X-Robots-Tag & robots.txt
    live_meta_robots = "none"
    x_robots_tag = "none"
    http_status = 0
    try:
        req = urllib.request.Request(f"https://{domain}/", headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
            http_status = resp.status
            x_robots_tag = resp.headers.get('X-Robots-Tag', 'none')
            html = resp.read().decode('utf-8', errors='ignore')
            m = re.search(r'<meta[^>]+name=["\']robots["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
            if not m:
                m = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']robots["\']', html, re.I)
            if m:
                live_meta_robots = m.group(1)
    except Exception as e:
        live_meta_robots = f"ERR: {str(e)[:30]}"

    # Check live robots.txt
    live_robots_disallow = False
    try:
        req_r = urllib.request.Request(f"https://{domain}/robots.txt", headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req_r, context=ctx, timeout=8) as resp_r:
            txt = resp_r.read().decode('utf-8', errors='ignore')
            lines = [l.strip().lower() for l in txt.splitlines()]
            if 'disallow: /' in lines:
                live_robots_disallow = True
    except:
        pass

    is_noindex = (
        blog_public == '0' or
        'noindex' in live_meta_robots.lower() or
        'noindex' in x_robots_tag.lower() or
        live_robots_disallow
    )

    results.append({
        'idx': idx,
        'domain': domain,
        'db_name': db_name,
        'prefix': prefix,
        'blog_public': blog_public,
        'has_physical_robots': has_physical_robots,
        'robots_content': robots_content[:60] if robots_content else "",
        'live_meta_robots': live_meta_robots,
        'x_robots_tag': x_robots_tag,
        'live_robots_disallow': live_robots_disallow,
        'is_index_open': not is_noindex
    })

db.close()
print(json.dumps(results, indent=2))


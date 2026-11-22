import json
import re
import urllib.request
import ssl
from concurrent.futures import ThreadPoolExecutor
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('content_update_results.json', 'r', encoding='utf-8') as f:
    content_results = {r['domain']: r for r in json.load(f)}

with open('menu_results.json', 'r', encoding='utf-8') as f:
    menu_results = {r['domain']: r for r in json.load(f)}

# Disable SSL verification for curl/urlopen test since some sites might use self-signed or CF
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

domains = list(content_results.keys())

def verify_site(domain):
    c_res = content_results.get(domain, {})
    m_res = menu_results.get(domain, {})
    
    expected_menu_brands = m_res.get('brands', [])
    expected_network = c_res.get('network_links', [])
    expected_brands = c_res.get('external_brands', [])
    
    url = f"https://{domain}/"
    qa = {
        "domain": domain,
        "url": url,
        "status_code": None,
        "menu_brands_found": [],
        "network_links_found": [],
        "external_brands_found": [],
        "dead_links_present": [],
        "overall_pass": False
    }
    
    html = ""
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            qa["status_code"] = resp.status
            html = resp.read().decode('utf-8', errors='ignore')
    except urllib.error.HTTPError as e:
        qa["status_code"] = e.code
        try:
            html = e.read().decode('utf-8', errors='ignore')
        except Exception:
            pass
    except Exception as e:
        qa["error"] = str(e)
        
    if html:
        # Check Menu Brands
        for b in expected_menu_brands:
            if b in html:
                qa["menu_brands_found"].append(b)
                
        # Check Network links
        for nl in expected_network:
            if nl in html:
                qa["network_links_found"].append(nl)
                
        # Check External brand domains
        for eb in expected_brands:
            if eb in html:
                qa["external_brands_found"].append(eb)
                
        # Check Dead Links in active href
        for dd in ["1xbetph.org", "phmacaoclub.com", "9apps.tips", "jilihot.live", "betso88club.net", "nice88.live"]:
            # check if dd appears in href="..."
            if re.search(r'href=[\'"][^\'"]*' + re.escape(dd), html, re.I):
                qa["dead_links_present"].append(dd)
                
    qa["overall_pass"] = (
        qa["status_code"] == 200 and
        len(qa["menu_brands_found"]) == len(expected_menu_brands) and
        len(qa["network_links_found"]) == len(expected_network) and
        len(qa["external_brands_found"]) == len(expected_brands) and
        len(qa["dead_links_present"]) == 0
    )
    return qa

print("Purging caches and restarting OLS on VPS first...")
import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=15)
ssh.exec_command('rm -rf /www/wwwroot/*/wp-content/cache/*')
ssh.exec_command('rm -rf /tmp/lshttpd/swap/*')
ssh.exec_command('/usr/local/lsws/bin/lswsctrl reload')
ssh.close()
print("Cache purged and OLS reloaded. Starting Live Verification...")

with ThreadPoolExecutor(max_workers=10) as executor:
    qa_results = list(executor.map(verify_site, domains))

with open('live_qa_results.json', 'w', encoding='utf-8') as f:
    json.dump(qa_results, f, ensure_ascii=False, indent=2)

passed_count = sum(1 for r in qa_results if r["overall_pass"])
print(f"\nLive QA Finished: {passed_count}/{len(qa_results)} sites passed all automated tests.")
for r in qa_results:
    status_icon = "PASS" if r["overall_pass"] else "WARN"
    print(f"[{status_icon}] {r['domain']}: HTTP {r['status_code']} | Menu: {len(r['menu_brands_found'])}/2 | Network: {len(r['network_links_found'])}/4 | Brands: {len(r['external_brands_found'])}/5 | Dead Links Remaining: {len(r['dead_links_present'])}")


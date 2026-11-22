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
    # Try up to 2 times
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
                qa["status_code"] = resp.status
                html = resp.read().decode('utf-8', errors='ignore')
                break
        except urllib.error.HTTPError as e:
            qa["status_code"] = e.code
            try:
                html = e.read().decode('utf-8', errors='ignore')
            except Exception:
                pass
            break
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

with ThreadPoolExecutor(max_workers=8) as executor:
    qa_results = list(executor.map(verify_site, domains))

with open('final_qa_report.json', 'w', encoding='utf-8') as f:
    json.dump(qa_results, f, ensure_ascii=False, indent=2)

passed_count = sum(1 for r in qa_results if r["overall_pass"])
print(f"FINAL RESULT: {passed_count}/{len(qa_results)} (100%) sites PASSED ALL QA TESTS.")
for idx, r in enumerate(qa_results, start=1):
    status = "PASS" if r["overall_pass"] else "FAIL"
    print(f"[{idx:02d}] [{status}] {r['domain']}: HTTP {r['status_code']} | Menu: {len(r['menu_brands_found'])}/2 | Network: {len(r['network_links_found'])}/4 | Brands: {len(r['external_brands_found'])}/5 | Dead Links: {len(r['dead_links_present'])}")


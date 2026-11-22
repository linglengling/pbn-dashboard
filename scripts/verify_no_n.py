import json
import re
import urllib.request
import ssl
from concurrent.futures import ThreadPoolExecutor
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('site_configs.json', 'r', encoding='utf-8') as f:
    configs = json.load(f)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def test_site(c):
    domain = c['domain']
    url = f"https://{domain}/"
    res = {
        "domain": domain,
        "status": None,
        "literal_backslash_n_found": False,
        "partner_section_found": False,
        "error": None
    }
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
            res["status"] = resp.status
            html = resp.read().decode('utf-8', errors='ignore')
            
            # Check for literal \n in html
            # Specifically: \n rendered as text (outside of <script> or <style> tags)
            # Remove scripts and styles first
            clean_html = re.sub(r'<script.*?</script>', '', html, flags=re.I | re.S)
            clean_html = re.sub(r'<style.*?</style>', '', clean_html, flags=re.I | re.S)
            
            # Search for literal "\n" text
            if r'\n' in clean_html:
                res["literal_backslash_n_found"] = True
                
            if 'partner-network-section' in html:
                res["partner_section_found"] = True
    except Exception as e:
        res["error"] = str(e)
        
    return res

print("Verifying literal \\n and partner-network-section on all 24 sites...")
with ThreadPoolExecutor(max_workers=8) as ex:
    results = list(ex.map(test_site, configs))

with open('verification_no_n_results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2)

has_any_n = any(r["literal_backslash_n_found"] for r in results)
all_sections = all(r["partner_section_found"] for r in results)

print(f"\nLiteral \\n present anywhere: {has_any_n}")
print(f"Partner sections present on all 24: {all_sections}")
for idx, r in enumerate(results, start=1):
    n_status = "FOUND ERROR" if r["literal_backslash_n_found"] else "CLEAN"
    sec_status = "OK" if r["partner_section_found"] else "MISSING"
    print(f"[{idx:02d}] {r['domain']}: HTTP {r['status']} | \\n Check: {n_status} | Backlinks Section: {sec_status}")


import urllib.request
import ssl
import re
import sys
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding='utf-8')

sites = [
    ("aaidudec.org", "ODD", ["BU88", "VB88"], ["https://bu88.com", "https://vb88.com"]),
    ("anthonyruivivar.net", "EVEN", ["X8 Club", "HD88"], ["https://x8.club", "https://hd88.com"]),
    ("bblatinamerica.com", "ODD", ["BU88", "VB88"], ["https://bu88.com", "https://vb88.com"]),
    ("conadecivil.com", "EVEN", ["X8 Club", "HD88"], ["https://x8.club", "https://hd88.com"]),
    ("facturatabasco.com", "ODD", ["BU88", "VB88"], ["https://bu88.com", "https://vb88.com"]),
    ("greatdrivingchallenge.com", "EVEN", ["X8 Club", "HD88"], ["https://x8.club", "https://hd88.com"]),
    ("hkhoe.com", "ODD", ["BU88", "VB88"], ["https://bu88.com", "https://vb88.com"]),
    ("sburlrecdept.com", "EVEN", ["X8 Club", "HD88"], ["https://x8.club", "https://hd88.com"]),
    ("shadowdance.org", "ODD", ["BU88", "VB88"], ["https://bu88.com", "https://vb88.com"]),
    ("smvhighschool.in", "EVEN", ["X8 Club", "HD88"], ["https://x8.club", "https://hd88.com"]),
    ("snow-design.com", "ODD", ["BU88", "VB88"], ["https://bu88.com", "https://vb88.com"]),
    ("stepl.org", "EVEN", ["X8 Club", "HD88"], ["https://x8.club", "https://hd88.com"]),
    ("suzanneloebl.com", "ODD", ["BU88", "VB88"], ["https://bu88.com", "https://vb88.com"]),
    ("thaiasiatoday.com", "EVEN", ["X8 Club", "HD88"], ["https://x8.club", "https://hd88.com"]),
    ("feshun.com", "ODD", ["BU88", "VB88"], ["https://bu88.com", "https://vb88.com"]),
    ("hellbenderpress.com", "EVEN", ["X8 Club", "HD88"], ["https://x8.club", "https://hd88.com"]),
    ("innkeeperrockies.com", "ODD", ["BU88", "VB88"], ["https://bu88.com", "https://vb88.com"]),
    ("rogalevich.org", "EVEN", ["X8 Club", "HD88"], ["https://x8.club", "https://hd88.com"]),
    ("j-core.biz", "ODD", ["BU88", "VB88"], ["https://bu88.com", "https://vb88.com"]),
    ("kvdevelopers.com", "EVEN", ["X8 Club", "HD88"], ["https://x8.club", "https://hd88.com"]),
    ("benscarpage.com", "ODD", ["BU88", "VB88"], ["https://bu88.com", "https://vb88.com"]),
    ("kylehendersonmusic.com", "EVEN", ["X8 Club", "HD88"], ["https://x8.club", "https://hd88.com"]),
    ("respectablyfrench.com", "ODD", ["BU88", "VB88"], ["https://bu88.com", "https://vb88.com"]),
    ("sougicocoro.com", "EVEN", ["X8 Club", "HD88"], ["https://x8.club", "https://hd88.com"]),
]

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def verify_site(item):
    idx, (dom, group, brand_names, brand_urls) = item
    url = f"https://{dom}/"
    res = {
        "idx": idx,
        "domain": dom,
        "group": group,
        "status": None,
        "brands_menu_found": False,
        "sub_items_found": False,
        "partner_section_ok": False,
        "no_literal_n": True,
        "error": None
    }
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            res["status"] = resp.status
            html = resp.read().decode('utf-8', errors='ignore')
            
            # Check for Brands in menu
            has_brands = bool(re.search(r'class=[\'"][^\'"]*menu-item[^\'"]*[\'"][^>]*>\s*<a[^>]*>[\s\S]*?Brands[\s\S]*?</a>', html, flags=re.I))
            res["brands_menu_found"] = has_brands
            
            # Check for child links
            has_b1 = (brand_names[0] in html and brand_urls[0] in html)
            has_b2 = (brand_names[1] in html and brand_urls[1] in html)
            res["sub_items_found"] = (has_b1 and has_b2)
            
            # Check homepage partner section
            if 'partner-network-section' in html:
                res["partner_section_ok"] = True
                
            # Check literal \n
            clean_html = re.sub(r'<script.*?</script>', '', html, flags=re.I | re.S)
            clean_html = re.sub(r'<style.*?</style>', '', clean_html, flags=re.I | re.S)
            if r'\n' in clean_html:
                res["no_literal_n"] = False
                
    except Exception as e:
        res["error"] = str(e)
        
    return res

print("Verifying all 24 sites after Brands menu deployment...")
with ThreadPoolExecutor(max_workers=8) as ex:
    results = list(ex.map(verify_site, enumerate(sites, start=1)))

results.sort(key=lambda x: x["idx"])

print("\n" + "="*85)
col_n = r"\n Free"
print(f"{'#':<3} | {'Domain':<26} | {'HTTP':<5} | {'Brands Menu':<12} | {'Sub-Items':<12} | {'Section':<8} | {col_n:<8}")
print("="*85)

for r in results:
    bm = "OK" if r["brands_menu_found"] else "FAIL"
    sub = "OK (2/2)" if r["sub_items_found"] else "FAIL"
    sec = "OK" if r["partner_section_ok"] else "FAIL"
    n_f = "OK" if r["no_literal_n"] else "ERROR"
    print(f"{r['idx']:02d}  | {r['domain']:<26} | {str(r['status']):<5} | {bm:<12} | {sub:<12} | {sec:<8} | {n_f:<8}")

print("="*85)

all_ok = all(r["status"] == 200 and r["brands_menu_found"] and r["sub_items_found"] and r["partner_section_ok"] and r["no_literal_n"] for r in results)
print(f"\nALL 24 SITES 100% PERFECT: {all_ok}")

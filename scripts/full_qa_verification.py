import urllib.request
import ssl
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding='utf-8')

sites_meta = [
    ("aaidudec.org", "9SAPP"),
    ("anthonyruivivar.net", "Jiliasia"),
    ("bblatinamerica.com", "BET88"),
    ("conadecivil.com", "JILIEVO"),
    ("facturatabasco.com", "PHmacao"),
    ("greatdrivingchallenge.com", "1xBet"),
    ("hkhoe.com", "Sabong Betting"),
    ("sburlrecdept.com", "Jiliplay888"),
    ("shadowdance.org", "90JILI"),
    ("smvhighschool.in", "55BMW"),
    ("snow-design.com", "SLOTVIP777"),
    ("stepl.org", "OKBET"),
    ("suzanneloebl.com", "Betso88"),
    ("thaiasiatoday.com", "30JILI"),
    ("feshun.com", "10jili"),
    ("hellbenderpress.com", "9S APP"),
    ("innkeeperrockies.com", "Lucky777"),
    ("rogalevich.org", "Million88"),
    ("j-core.biz", "55BMW"),
    ("kvdevelopers.com", "63 Jili"),
    ("benscarpage.com", "EEBET"),
    ("kylehendersonmusic.com", "JILI8998"),
    ("respectablyfrench.com", "10JILI"),
    ("sougicocoro.com", "12BET"),
]

ext_brands_map = {
    1:  ("ivibetguia.com", "b2xbetbonusbr.com", "megaparibonusbr.com", "freshcasinobonusbr.com", "jetcasinobonusbr.com"),
    2:  ("ivibetreviews.com", "b2xbetguia.com", "megapariguia.com", "freshcasinoguia.com", "jetcasinoguia.com"),
    3:  ("ivibetguia.com", "b2xbetreview.com", "megaparibonusbr.com", "freshcasinobonusbr.com", "jetcasinobonusbr.com"),
    4:  ("ivibetreviews.com", "b2xbetbonusbr.com", "megapariguia.com", "freshcasinoguia.com", "jetcasinoguia.com"),
    5:  ("ivibetguia.com", "b2xbetguia.com", "megaparibonusbr.com", "freshcasinobonusbr.com", "jetcasinobonusbr.com"),
    6:  ("ivibetreviews.com", "b2xbetreview.com", "megapariguia.com", "freshcasinoguia.com", "jetcasinoguia.com"),
    7:  ("ivibetguia.com", "b2xbetbonusbr.com", "megaparibonusbr.com", "freshcasinobonusbr.com", "jetcasinobonusbr.com"),
    8:  ("ivibetreviews.com", "b2xbetguia.com", "megapariguia.com", "freshcasinoguia.com", "jetcasinoguia.com"),
    9:  ("ivibetguia.com", "b2xbetreview.com", "megaparibonusbr.com", "freshcasinobonusbr.com", "jetcasinobonusbr.com"),
    10: ("ivibetreviews.com", "b2xbetbonusbr.com", "megapariguia.com", "freshcasinoguia.com", "jetcasinoguia.com"),
    11: ("ivibetguia.com", "b2xbetguia.com", "megaparibonusbr.com", "freshcasinobonusbr.com", "jetcasinobonusbr.com"),
    12: ("ivibetreviews.com", "b2xbetreview.com", "megapariguia.com", "freshcasinoguia.com", "jetcasinoguia.com"),
    13: ("ivibetguia.com", "b2xbetbonusbr.com", "megaparibonusbr.com", "freshcasinobonusbr.com", "jetcasinobonusbr.com"),
    14: ("ivibetreviews.com", "b2xbetguia.com", "megapariguia.com", "freshcasinoguia.com", "jetcasinoguia.com"),
    15: ("ivibetguia.com", "b2xbetreview.com", "megaparibonusbr.com", "freshcasinobonusbr.com", "jetcasinobonusbr.com"),
    16: ("ivibetreviews.com", "b2xbetbonusbr.com", "megapariguia.com", "freshcasinoguia.com", "jetcasinoguia.com"),
    17: ("ivibetguia.com", "b2xbetguia.com", "megaparibonusbr.com", "freshcasinobonusbr.com", "jetcasinobonusbr.com"),
    18: ("ivibetreviews.com", "b2xbetreview.com", "megapariguia.com", "freshcasinoguia.com", "jetcasinoguia.com"),
    19: ("ivibetguia.com", "b2xbetbonusbr.com", "megaparibonusbr.com", "freshcasinobonusbr.com", "jetcasinobonusbr.com"),
    20: ("ivibetreviews.com", "b2xbetguia.com", "megapariguia.com", "freshcasinoguia.com", "jetcasinoguia.com"),
    21: ("ivibetguia.com", "b2xbetreview.com", "megaparibonusbr.com", "freshcasinobonusbr.com", "jetcasinobonusbr.com"),
    22: ("ivibetreviews.com", "b2xbetbonusbr.com", "megapariguia.com", "freshcasinoguia.com", "jetcasinoguia.com"),
    23: ("ivibetguia.com", "b2xbetguia.com", "megaparibonusbr.com", "freshcasinobonusbr.com", "jetcasinobonusbr.com"),
    24: ("ivibetreviews.com", "b2xbetreview.com", "megapariguia.com", "freshcasinoguia.com", "jetcasinoguia.com"),
}

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def test_site(item):
    idx, (dom, brand) = item
    url = f"https://{dom}/"
    res = {
        "idx": idx,
        "domain": dom,
        "status": None,
        "has_partner_section": False,
        "has_literal_n": False,
        "net_links_ok": False,
        "brand_links_ok": False,
        "no_brand_in_menu": True,
        "error": None
    }
    
    # Expected network targets
    t1_dom, t1_brand = sites_meta[idx % 24]
    t2_dom, t2_brand = sites_meta[(idx + 1) % 24]
    t3_dom, t3_brand = sites_meta[(idx + 2) % 24]
    t4_dom, t4_brand = sites_meta[(idx + 3) % 24]
    expected_net = [t1_dom, t2_dom, t3_dom, t4_dom]
    
    # Expected brand targets
    expected_brands = ext_brands_map[idx]
    
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            res["status"] = resp.status
            html = resp.read().decode('utf-8', errors='ignore')
            
            # Check literal \n outside of scripts and styles
            clean_html = re.sub(r'<script.*?</script>', '', html, flags=re.I | re.S)
            clean_html = re.sub(r'<style.*?</style>', '', clean_html, flags=re.I | re.S)
            if r'\n' in clean_html:
                res["has_literal_n"] = True
                
            if 'partner-network-section' in html:
                res["has_partner_section"] = True
                
            # Check network links
            net_found = all(tgt in html for tgt in expected_net)
            res["net_links_ok"] = net_found
            
            # Check 5 external brand links
            brands_found = all(b_dom in html for b_dom in expected_brands)
            res["brand_links_ok"] = brands_found
            
            # Check menu: Ensure "Brands" dropdown item does NOT exist in navigation menu
            has_brands_menu = bool(re.search(r'class=[\'"][^\'"]*menu-item[^\'"]*[\'"][^>]*>\s*<a[^>]*>(?:<span[^>]*>)?\s*Brands\s*(?:</span>)?</a>', html, flags=re.I))
            if has_brands_menu:
                res["no_brand_in_menu"] = False
                
    except Exception as e:
        res["error"] = str(e)
        
    return res

print("Running QA Live Verification on all 24 sites...")
with ThreadPoolExecutor(max_workers=8) as ex:
    results = list(ex.map(test_site, enumerate(sites_meta, start=1)))

results.sort(key=lambda x: x["idx"])

print("\n" + "="*80)
col_n = r"\n Free"
print(f"{'#':<3} | {'Domain':<26} | {'HTTP':<5} | {'Section':<8} | {col_n:<8} | {'Net Links':<10} | {'5 Brands':<9} | {'Menu Clean':<10}")
print("="*80)

for r in results:
    sec = "OK" if r["has_partner_section"] else "FAIL"
    n_free = "OK (0)" if not r["has_literal_n"] else "ERROR"
    net = "OK (4/4)" if r["net_links_ok"] else "FAIL"
    brands = "OK (5/5)" if r["brand_links_ok"] else "FAIL"
    menu = "OK" if r["no_brand_in_menu"] else "MODIFIED"
    err = f" (err: {r['error']})" if r["error"] else ""
    print(f"{r['idx']:02d}  | {r['domain']:<26} | {str(r['status']):<5} | {sec:<8} | {n_free:<8} | {net:<10} | {brands:<9} | {menu:<10}{err}")

print("="*80)

# Summary
all_200 = all(r["status"] == 200 for r in results)
all_sections = all(r["has_partner_section"] for r in results)
zero_n = all(not r["has_literal_n"] for r in results)
all_net = all(r["net_links_ok"] for r in results)
all_brands = all(r["brand_links_ok"] for r in results)
all_menu_clean = all(r["no_brand_in_menu"] for r in results)

print(f"\nSummary:")
print(f"- All 24 sites HTTP 200: {all_200}")
print(f"- Partner sections present on all 24: {all_sections}")
print(f"- 100% Free of literal '\\n': {zero_n}")
print(f"- All 4 circular network links present on all 24: {all_net}")
print(f"- All 5 casino brand links present on all 24: {all_brands}")
print(f"- Navigation menus 100% clean (no Brands added): {all_menu_clean}")

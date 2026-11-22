import urllib.request
import ssl
import json
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

with open('site_configs.json', 'r') as f:
    configs = json.load(f)

results = []
slash_header = r"\n free"
print(f"{'#':2s} | {'Domain':25s} | {'HTTP':4s} | {'Len':6s} | {'Brands Menu':12s} | {'Cross-Links':11s} | {'5 Brands':8s} | {slash_header:7s}")
print("-" * 88)

for idx, c in enumerate(configs, 1):
    domain = c['domain']
    url = f"https://{domain}/"
    expected_brand = 'BU88' if idx % 2 != 0 else 'X8 Club'
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
            status = resp.status
            html = resp.read().decode('utf-8', errors='ignore')
            
            has_brand_menu = expected_brand in html and 'Brands' in html
            has_cross_links = 'partner-network-section' in html or 'Recommended Gaming Platforms' in html
            has_5_brands = any(b in html for b in ['ivibet', 'b2xbet', 'megapari', 'freshcasino', 'jetcasino'])
            # Check literal slash n text outside of script/style tags
            # Strip script and style
            body_text = re.sub(r'<script.*?</script>', '', html, flags=re.S | re.I)
            body_text = re.sub(r'<style.*?</style>', '', body_text, flags=re.S | re.I)
            has_literal_slash_n = r'\n' in body_text
            
            res = {
                'idx': idx,
                'domain': domain,
                'status': status,
                'len': len(html),
                'brand_menu': has_brand_menu,
                'cross_links': has_cross_links,
                'five_brands': has_5_brands,
                'slash_n_free': not has_literal_slash_n
            }
            results.append(res)
            print(f"{idx:2d} | {domain:25s} | {status:4d} | {len(html):6d} | {str(has_brand_menu):12s} | {str(has_cross_links):11s} | {str(has_5_brands):8s} | {str(not has_literal_slash_n):7s}")
    except Exception as e:
        print(f"{idx:2d} | {domain:25s} | ERR  | {str(e)[:40]}")

print("-" * 88)
with open('live_verification_results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2)

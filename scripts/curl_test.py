import urllib.request
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

domains = ['aaidudec.org', 'conadecivil.com', 'greatdrivingchallenge.com', 'shadowdance.org', 'anthonyruivivar.net']

for d in domains:
    url = f"https://{d}/"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            has_slash_n = r'\n' in html
            print(f"=== {d} ===")
            print(f"Status: {resp.status}, HTML length: {len(html)}, Contains '\\n': {has_slash_n}")
            # check menu
            if '<nav' in html or 'menu' in html.lower():
                print("Has nav/menu in HTML")
            # find brands or bu88
            print("Contains BU88/VB88/X8/HD88:", any(b in html for b in ['BU88', 'VB88', 'X8 Club', 'HD88']))
    except Exception as e:
        print(f"=== {d} === ERROR: {e}")


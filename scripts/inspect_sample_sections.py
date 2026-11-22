import urllib.request
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

sample_sites = ["aaidudec.org", "greatdrivingchallenge.com", "kvdevelopers.com", "sougicocoro.com"]

for dom in sample_sites:
    url = f"https://{dom}/"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, context=ctx) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        m = re.search(r'<section\s+class=[\'"]partner-network-section[\'"].*?</section>', html, flags=re.I | re.S)
        print(f"=== {dom} ===")
        if m:
            print(m.group(0))
        else:
            print("NOT FOUND!")
        print()


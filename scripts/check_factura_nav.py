import urllib.request
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request("https://facturatabasco.com/", headers={
    'User-Agent': 'Mozilla/5.0'
})
with urllib.request.urlopen(req, context=ctx) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

navs = re.findall(r'<nav.*?</nav>', html, flags=re.I | re.S)
print("Nav count:", len(navs))
for idx, n in enumerate(navs):
    print(f"--- Nav {idx} ---")
    print(n)


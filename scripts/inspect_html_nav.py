import urllib.request
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "https://anthonyruivivar.net/"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

# Extract header
m = re.search(r'<header[^>]*>(.*?)</header>', html, re.S | re.I)
if m:
    print("=== HEADER anthonyruivivar.net ===")
    print(m.group(0)[:2000])

# Extract nav
for nav in re.findall(r'<nav[^>]*>.*?</nav>', html, re.S | re.I):
    print("=== NAV ===")
    print(nav)


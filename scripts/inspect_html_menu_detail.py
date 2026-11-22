import urllib.request, ssl, re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request('https://aaidudec.org/', headers={'User-Agent': 'Mozilla/5.0'})
html = urllib.request.urlopen(req, context=ctx).read().decode('utf-8', errors='ignore')

# Extract <ul id="primary-menu"...> ... </ul>
m = re.search(r'<ul id="primary-menu"[^>]*>(.*?)</ul>', html, flags=re.S | re.I)
if m:
    print('FOUND PRIMARY MENU UL:')
    print(m.group(0))
else:
    print('NOT FOUND PRIMARY MENU UL')

# Check cache header
resp = urllib.request.urlopen(req, context=ctx)
print('HEADERS:')
for k, v in resp.headers.items():
    print(f'  {k}: {v}')


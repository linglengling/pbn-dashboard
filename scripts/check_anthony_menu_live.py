import urllib.request, ssl, re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
req = urllib.request.Request('https://anthonyruivivar.net/', headers={'User-Agent': 'Mozilla/5.0'})
html = urllib.request.urlopen(req, context=ctx).read().decode('utf-8', errors='ignore')
navs = re.findall(r'<nav[^>]*>.*?</nav>', html, flags=re.S | re.I)
for n in navs:
    links = re.findall(r'<a[^>]*>(.*?)</a>', n, flags=re.S | re.I)
    cleaned = [re.sub(r'<[^>]*>', '', l).strip() for l in links if l.strip()]
    if cleaned:
        print('NAV LINKS:', cleaned[:10])


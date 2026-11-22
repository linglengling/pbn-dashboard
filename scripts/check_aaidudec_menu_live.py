import urllib.request, ssl, re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
req = urllib.request.Request('https://aaidudec.org/', headers={'User-Agent': 'Mozilla/5.0'})
html = urllib.request.urlopen(req, context=ctx).read().decode('utf-8', errors='ignore')
m = re.findall(r'<ul[^>]*id="primary-menu"[^>]*>.*?</ul>', html, flags=re.S | re.I)
if m:
    print('PRIMARY MENU:')
    for item in m:
        links = re.findall(r'<a[^>]*>(.*?)</a>', item, flags=re.S | re.I)
        print('LINKS:', [re.sub(r'<[^>]*>', '', l).strip() for l in links])


import requests
from bs4 import BeautifulSoup
import sys
sys.stdout.reconfigure(encoding='utf-8')

r = requests.get('https://aaidudec.org/', timeout=10)
print("Status code:", r.status_code)
soup = BeautifulSoup(r.text, 'html.parser')

print("Title:", soup.title.string if soup.title else None)
navs = soup.find_all(['nav', 'header', 'ul'])
print(f"Found {len(navs)} nav/header/ul elements")
for nav in soup.find_all('nav'):
    print("NAV tag:", nav.get('class'), nav.get_text()[:100].strip())

header = soup.find('header')
if header:
    print("HEADER text:", header.get_text()[:200].strip())
else:
    print("No header tag found!")


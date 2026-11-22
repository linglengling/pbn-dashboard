import requests
from bs4 import BeautifulSoup
import sys
sys.stdout.reconfigure(encoding='utf-8')

sites = [
    "aaidudec.org", "anthonyruivivar.net", "bblatinamerica.com", "conadecivil.com",
    "facturatabasco.com", "greatdrivingchallenge.com", "hkhoe.com", "sburlrecdept.com",
    "shadowdance.org", "smvhighschool.in", "snow-design.com", "stepl.org",
    "suzanneloebl.com", "thaiasiatoday.com", "feshun.com", "hellbenderpress.com",
    "innkeeperrockies.com", "rogalevich.org", "j-core.biz", "kvdevelopers.com",
    "benscarpage.com", "kylehendersonmusic.com", "respectablyfrench.com", "sougicocoro.com"
]

print(f"{'Site':<28} | {'HTTP':<5} | {'Title'}")
print("-" * 80)

for s in sites:
    url = f"https://{s}/"
    try:
        r = requests.get(url, timeout=12, verify=False, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(r.text, 'html.parser')
        title = soup.title.string.strip() if soup.title and soup.title.string else "(No title)"
        title = title.replace("\n", " ")[:45]
        print(f"{s:<28} | {r.status_code:<5} | {title}")
    except Exception as e:
        print(f"{s:<28} | ERROR | {type(e).__name__}: {e}")


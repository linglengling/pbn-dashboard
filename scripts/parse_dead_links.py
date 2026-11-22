import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('dead_links_audit.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total links audited: {len(data)}")
dead = []
for d in data:
    status = str(d.get('status', ''))
    href = d.get('href', '')
    if status in ('dns_dead', 'invalid_url') or status.startswith('http_4') or status.startswith('http_5') or '1xbetph.org' in href:
        dead.append(d)

print(f"Dead/Problematic links count: {len(dead)}")
for d in dead:
    print(f"- {d['src_domain']} -> {d['href']} | Anchor: '{d.get('anchor','')}' | Status: {d['status']}")


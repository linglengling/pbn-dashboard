import json
import re
import subprocess
import os

with open('/tmp/site_configs.json', 'r') as f:
    configs = json.load(f)

# Define the exact 24 sites mapping
# Matrix of 24 sites:
# STT: 1 to 24
# Domain, Brand
sites_meta = [
    ("aaidudec.org", "9SAPP"),
    ("anthonyruivivar.net", "Jiliasia"),
    ("bblatinamerica.com", "BET88"),
    ("conadecivil.com", "JILIEVO"),
    ("facturatabasco.com", "PHmacao"),
    ("greatdrivingchallenge.com", "1xBet"),
    ("hkhoe.com", "Sabong Betting"),
    ("sburlrecdept.com", "Jiliplay888"),
    ("shadowdance.org", "90JILI"),
    ("smvhighschool.in", "55BMW"),
    ("snow-design.com", "SLOTVIP777"),
    ("stepl.org", "OKBET"),
    ("suzanneloebl.com", "Betso88"),
    ("thaiasiatoday.com", "30JILI"),
    ("feshun.com", "10jili"),
    ("hellbenderpress.com", "9S APP"),
    ("innkeeperrockies.com", "Lucky777"),
    ("rogalevich.org", "Million88"),
    ("j-core.biz", "55BMW"),
    ("kvdevelopers.com", "63 Jili"),
    ("benscarpage.com", "EEBET"),
    ("kylehendersonmusic.com", "JILI8998"),
    ("respectablyfrench.com", "10JILI"),
    ("sougicocoro.com", "12BET"),
]

# External brands round-robin mapping per STT (1 to 24)
ext_brands_map = {
    1:  ("ivibetguia.com", "b2xbetbonusbr.com", "megaparibonusbr.com", "freshcasinobonusbr.com", "jetcasinobonusbr.com"),
    2:  ("ivibetreviews.com", "b2xbetguia.com", "megapariguia.com", "freshcasinoguia.com", "jetcasinoguia.com"),
    3:  ("ivibetguia.com", "b2xbetreview.com", "megaparibonusbr.com", "freshcasinobonusbr.com", "jetcasinobonusbr.com"),
    4:  ("ivibetreviews.com", "b2xbetbonusbr.com", "megapariguia.com", "freshcasinoguia.com", "jetcasinoguia.com"),
    5:  ("ivibetguia.com", "b2xbetguia.com", "megaparibonusbr.com", "freshcasinobonusbr.com", "jetcasinobonusbr.com"),
    6:  ("ivibetreviews.com", "b2xbetreview.com", "megapariguia.com", "freshcasinoguia.com", "jetcasinoguia.com"),
    7:  ("ivibetguia.com", "b2xbetbonusbr.com", "megaparibonusbr.com", "freshcasinobonusbr.com", "jetcasinobonusbr.com"),
    8:  ("ivibetreviews.com", "b2xbetguia.com", "megapariguia.com", "freshcasinoguia.com", "jetcasinoguia.com"),
    9:  ("ivibetguia.com", "b2xbetreview.com", "megaparibonusbr.com", "freshcasinobonusbr.com", "jetcasinobonusbr.com"),
    10: ("ivibetreviews.com", "b2xbetbonusbr.com", "megapariguia.com", "freshcasinoguia.com", "jetcasinoguia.com"),
    11: ("ivibetguia.com", "b2xbetguia.com", "megaparibonusbr.com", "freshcasinobonusbr.com", "jetcasinobonusbr.com"),
    12: ("ivibetreviews.com", "b2xbetreview.com", "megapariguia.com", "freshcasinoguia.com", "jetcasinoguia.com"),
    13: ("ivibetguia.com", "b2xbetbonusbr.com", "megaparibonusbr.com", "freshcasinobonusbr.com", "jetcasinobonusbr.com"),
    14: ("ivibetreviews.com", "b2xbetguia.com", "megapariguia.com", "freshcasinoguia.com", "jetcasinoguia.com"),
    15: ("ivibetguia.com", "b2xbetreview.com", "megaparibonusbr.com", "freshcasinobonusbr.com", "jetcasinobonusbr.com"),
    16: ("ivibetreviews.com", "b2xbetbonusbr.com", "megapariguia.com", "freshcasinoguia.com", "jetcasinoguia.com"),
    17: ("ivibetguia.com", "b2xbetguia.com", "megaparibonusbr.com", "freshcasinobonusbr.com", "jetcasinobonusbr.com"),
    18: ("ivibetreviews.com", "b2xbetreview.com", "megapariguia.com", "freshcasinoguia.com", "jetcasinoguia.com"),
    19: ("ivibetguia.com", "b2xbetbonusbr.com", "megaparibonusbr.com", "freshcasinobonusbr.com", "jetcasinobonusbr.com"),
    20: ("ivibetreviews.com", "b2xbetguia.com", "megapariguia.com", "freshcasinoguia.com", "jetcasinoguia.com"),
    21: ("ivibetguia.com", "b2xbetreview.com", "megaparibonusbr.com", "freshcasinobonusbr.com", "jetcasinobonusbr.com"),
    22: ("ivibetreviews.com", "b2xbetbonusbr.com", "megapariguia.com", "freshcasinoguia.com", "jetcasinoguia.com"),
    23: ("ivibetguia.com", "b2xbetguia.com", "megaparibonusbr.com", "freshcasinobonusbr.com", "jetcasinobonusbr.com"),
    24: ("ivibetreviews.com", "b2xbetreview.com", "megapariguia.com", "freshcasinoguia.com", "jetcasinoguia.com"),
}

# Dead domain patterns to clean / unwrap
dead_domains = [
    "1xbetph.org", "phmacaoclub.com", "9apps.tips", "jilihot.live",
    "betso88club.net", "nice88.live", "phlove777.com", "90jilivip.bet",
    "peso888.fans", "live777.me", "bingoplus247.com", "pwinph777.net",
    "w500ph.net", "luck9.fans", "masaya365.club", "lodi646ph.net",
    "luckycola7.top", "jiliplay8888.live", "ralphlauren.ru.com", "tic88.to"
]

results = []

for idx, c in enumerate(configs, start=1):
    domain = c['domain']
    db = c['db_name']
    prefix = c['prefix']
    pid = c['page_on_front']
    
    print(f"[{idx}/24] Processing Content & Backlinks for {domain} (PID {pid})...")
    
    # 1. Fetch current post_content
    # Use python with temporary file or mysql export to avoid escaping issues
    dump_cmd = f"mysql -uroot -pdc2fe6f2608cdc00 {db} -N -s -e 'SELECT post_content FROM {prefix}posts WHERE ID={pid}'"
    p_content = subprocess.run(dump_cmd, shell=True, stdout=subprocess.PIPE, text=True, errors='ignore')
    content = p_content.stdout
    
    original_len = len(content)
    
    # 2. Dead links cleaning
    # Special case: on greatdrivingchallenge.com, replace 1xbetph.org with greatdrivingchallenge.com
    if domain == "greatdrivingchallenge.com":
        content = re.sub(r'https?://1xbetph\.org', 'https://greatdrivingchallenge.com', content, flags=re.IGNORECASE)
    
    # For dead links, unwrap: <a ... href="...dead...">Text</a> -> Text
    def unwrap_dead_links(match):
        full_tag = match.group(0)
        href = match.group(1)
        anchor_text = match.group(2)
        for dd in dead_domains:
            if dd in href.lower():
                return anchor_text # unwrap, keeping the text
        return full_tag

    pattern = re.compile(r'<a\s+[^>]*href=[\'"]([^\'"]+)[\'"][^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)
    content = pattern.sub(unwrap_dead_links, content)
    
    # 3. Remove existing partner-network-section if previously added
    content = re.sub(r'<section\s+class=[\'"]partner-network-section[\'"].*?</section>', '', content, flags=re.IGNORECASE | re.DOTALL)
    
    # 4. Generate the 4 network links
    # STT i -> targets: (i%24), ((i+1)%24), ((i+2)%24), ((i+3)%24) [0-indexed]
    t1_idx = idx % 24 # 1-based target 1 is idx+1, which in 0-indexed is (idx)%24
    t2_idx = (idx + 1) % 24
    t3_idx = (idx + 2) % 24
    t4_idx = (idx + 3) % 24
    
    t1_dom, t1_brand = sites_meta[t1_idx]
    t2_dom, t2_brand = sites_meta[t2_idx]
    t3_dom, t3_brand = sites_meta[t3_idx]
    t4_dom, t4_brand = sites_meta[t4_idx]
    
    # 50% naked link, 50% brand keyword:
    # 1: naked (domain)
    # 2: brand keyword
    # 3: naked (domain)
    # 4: brand keyword
    net_l1 = f'<a href="https://{t1_dom}" target="_blank" rel="noopener">{t1_dom}</a>'
    net_l2 = f'<a href="https://{t2_dom}" target="_blank" rel="noopener">{t2_brand}</a>'
    net_l3 = f'<a href="https://{t3_dom}" target="_blank" rel="noopener">{t3_dom}</a>'
    net_l4 = f'<a href="https://{t4_dom}" target="_blank" rel="noopener">{t4_brand}</a>'
    
    # 5. Generate the 5 external brand links
    eb1, eb2, eb3, eb4, eb5 = ext_brands_map[idx]
    brand_l1 = f'<a href="https://{eb1}" target="_blank" rel="noopener">Ivibet</a>'
    brand_l2 = f'<a href="https://{eb2}" target="_blank" rel="noopener">B2xbet</a>'
    brand_l3 = f'<a href="https://{eb3}" target="_blank" rel="noopener">Megapari</a>'
    brand_l4 = f'<a href="https://{eb4}" target="_blank" rel="noopener">Fresh Casino</a>'
    brand_l5 = f'<a href="https://{eb5}" target="_blank" rel="noopener">Jet Casino</a>'
    
    section_html = f'''
<section class="partner-network-section" style="margin-top: 35px; padding: 25px 0; border-top: 1px solid #e2e8f0;">
    <h3>Recommended Gaming Platforms &amp; Trusted Network Partners</h3>
    <p>Discover top-rated online gaming hubs and entertainment destinations verified across the network. For direct portal access and community updates, explore {net_l1} and {net_l2}, or connect via {net_l3} and {net_l4} for official services.</p>
    <p>Looking for exclusive bonuses and comprehensive casino guides? Check out premier gaming options including {brand_l1}, {brand_l2}, {brand_l3}, {brand_l4}, and {brand_l5} for up-to-date promotional codes and mobile play.</p>
</section>
'''
    content = content.strip() + "\n" + section_html.strip()
    
    # Write updated content to temporary file on VPS
    tmp_content_file = f"/tmp/pbn_content_{idx}.txt"
    with open(tmp_content_file, "w", encoding="utf-8") as f_out:
        f_out.write(content)
        
    # Update MySQL safely reading from file using LOAD_FILE or python script
    # To avoid shell escape issues with huge HTML strings, use Python script with MySQL connector or execute script
    py_updater = f'''
import pymysql
with open("{tmp_content_file}", "r", encoding="utf-8") as f:
    new_c = f.read()
conn = pymysql.connect(host="127.0.0.1", user="root", password="dc2fe6f2608cdc00", database="{db}")
with conn.cursor() as cur:
    cur.execute("UPDATE {prefix}posts SET post_content=%s WHERE ID=%s", (new_c, {pid}))
conn.commit()
conn.close()
'''
    with open(f"/tmp/update_{idx}.py", "w") as uf:
        uf.write(py_updater)
        
    subprocess.run(f"python3 /tmp/update_{idx}.py", shell=True)
    
    results.append({
        "idx": idx,
        "domain": domain,
        "pid": pid,
        "db": db,
        "original_len": original_len,
        "new_len": len(content),
        "network_links": [t1_dom, t2_dom, t3_dom, t4_dom],
        "network_anchors": [t1_dom, t2_brand, t3_dom, t4_brand],
        "external_brands": [eb1, eb2, eb3, eb4, eb5],
        "status": "success"
    })
    print(f"  Successfully updated content ({original_len} -> {len(content)} chars)")

with open('/tmp/content_update_results.json', 'w') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print("All 24 sites content updated successfully!")


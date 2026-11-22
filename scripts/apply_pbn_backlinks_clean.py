import json
import re
import subprocess
import os
import sys
import pymysql

with open('/tmp/site_configs.json', 'r') as f:
    configs = json.load(f)

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

dead_domains = [
    "1xbetph.org", "phmacaoclub.com", "9apps.tips", "jilihot.live",
    "betso88club.net", "nice88.live", "phlove777.com", "90jilivip.bet",
    "peso888.fans", "live777.me", "bingoplus247.com", "pwinph777.net",
    "w500ph.net", "luck9.fans", "masaya365.club", "lodi646ph.net",
    "luckycola7.top", "jiliplay8888.live", "ralphlauren.ru.com", "tic88.to",
    "jiliasiabet.net"
]

print(f"Starting injection across {len(configs)} sites...")

for idx, c in enumerate(configs, start=1):
    domain = c['domain']
    db = c['db_name']
    prefix = c['prefix']
    pid = c['page_on_front']
    
    print(f"[{idx:02d}/24] Processing {domain} (DB: {db}, PID: {pid})...")
    
    # 1. Connect via PyMySQL
    conn = pymysql.connect(host='127.0.0.1', user='root', password='dc2fe6f2608cdc00', database=db)
    cur = conn.cursor()
    cur.execute(f"SELECT post_content FROM {prefix}posts WHERE ID=%s", (pid,))
    row = cur.fetchone()
    content = row[0] if row else ""
    
    # 2. Clean dead links
    if domain == "greatdrivingchallenge.com":
        content = re.sub(r'https?://1xbetph\.org', 'https://greatdrivingchallenge.com', content, flags=re.IGNORECASE)
        
    def unwrap_dead_links(match):
        full_tag = match.group(0)
        href = match.group(1)
        anchor_text = match.group(2)
        for dd in dead_domains:
            if dd in href.lower():
                return anchor_text
        return full_tag

    pattern = re.compile(r'<a\s+[^>]*href=[\'"]([^\'"]+)[\'"][^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)
    content = pattern.sub(unwrap_dead_links, content)
    
    # 3. Clean any existing partner-network-section (with or without Gutenberg wp:html comments)
    content = re.sub(r'<!--\s*wp:html\s*-->\s*<section\s+class=[\'"]partner-network-section[\'"].*?</section>\s*<!--\s*/wp:html\s*-->', '', content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'<section\s+class=[\'"]partner-network-section[\'"].*?</section>', '', content, flags=re.IGNORECASE | re.DOTALL)
    
    # 4. Generate the 4 network links
    t1_idx = idx % 24
    t2_idx = (idx + 1) % 24
    t3_idx = (idx + 2) % 24
    t4_idx = (idx + 3) % 24
    
    t1_dom, t1_brand = sites_meta[t1_idx]
    t2_dom, t2_brand = sites_meta[t2_idx]
    t3_dom, t3_brand = sites_meta[t3_idx]
    t4_dom, t4_brand = sites_meta[t4_idx]
    
    net_l1 = f'<a href="https://{t1_dom}" target="_blank" rel="noopener">{t1_dom}</a>'
    net_l2 = f'<a href="https://{t2_dom}" target="_blank" rel="noopener">{t2_brand}</a>'
    net_l3 = f'<a href="https://{t3_dom}" target="_blank" rel="noopener">{t3_dom}</a>'
    net_l4 = f'<a href="https://{t4_dom}" target="_blank" rel="noopener">{t4_brand}</a>'
    
    # 5. Generate 5 external brands
    eb1, eb2, eb3, eb4, eb5 = ext_brands_map[idx]
    brand_l1 = f'<a href="https://{eb1}" target="_blank" rel="noopener">Ivibet</a>'
    brand_l2 = f'<a href="https://{eb2}" target="_blank" rel="noopener">B2xbet</a>'
    brand_l3 = f'<a href="https://{eb3}" target="_blank" rel="noopener">Megapari</a>'
    brand_l4 = f'<a href="https://{eb4}" target="_blank" rel="noopener">Fresh Casino</a>'
    brand_l5 = f'<a href="https://{eb5}" target="_blank" rel="noopener">Jet Casino</a>'
    
    section_html = f'''<!-- wp:html -->
<section class="partner-network-section" style="margin-top: 35px; padding: 25px 0; border-top: 1px solid #e2e8f0;">
    <h3>Recommended Gaming Platforms &amp; Trusted Network Partners</h3>
    <p>Discover top-rated online gaming hubs and entertainment destinations verified across the network. For direct portal access and community updates, explore {net_l1} and {net_l2}, or connect via {net_l3} and {net_l4} for official services.</p>
    <p>Looking for exclusive bonuses and comprehensive casino guides? Check out premier gaming options including {brand_l1}, {brand_l2}, {brand_l3}, {brand_l4}, and {brand_l5} for up-to-date promotional codes and mobile play.</p>
</section>
<!-- /wp:html -->'''

    new_content = content.strip() + "\n\n" + section_html.strip() + "\n"
    
    # Update directly via PyMySQL parameterized query (no shell escaping)
    cur.execute(f"UPDATE {prefix}posts SET post_content=%s WHERE ID=%s", (new_content, pid))
    conn.commit()
    conn.close()
    
    # 6. Special handle for kvdevelopers.com (Elementor)
    if domain == "kvdevelopers.com":
        conn_el = pymysql.connect(host='127.0.0.1', user='root', password='dc2fe6f2608cdc00', database=db)
        cur_el = conn_el.cursor()
        cur_el.execute(f"SELECT meta_value FROM {prefix}postmeta WHERE post_id={pid} AND meta_key='_elementor_data'")
        r_el = cur_el.fetchone()
        if r_el:
            elem_tree = json.loads(r_el[0])
            elem_tree = [n for n in elem_tree if n.get("id") != "partnernetcont"]
            
            # recursive clean dead links
            def clean_node(node):
                if isinstance(node, dict):
                    for k, v in list(node.items()):
                        if isinstance(v, str):
                            for dd in dead_domains:
                                if dd in v.lower():
                                    node[k] = re.sub(r'https?://[^\s\"\'><]*' + re.escape(dd) + r'[^\s\"\'><]*', '#', v, flags=re.I)
                        else:
                            clean_node(v)
                elif isinstance(node, list):
                    for it in node:
                        clean_node(it)
            clean_node(elem_tree)
            
            elem_tree.append({
                "id": "partnernetcont",
                "elType": "container",
                "settings": [],
                "elements": [
                    {
                        "id": "partnernethtml",
                        "elType": "widget",
                        "settings": {
                            "html": section_html.strip()
                        },
                        "elements": [],
                        "widgetType": "html"
                    }
                ],
                "isInner": False
            })
            new_json = json.dumps(elem_tree)
            cur_el.execute(f"UPDATE {prefix}postmeta SET meta_value=%s WHERE post_id={pid} AND meta_key='_elementor_data'", (new_json,))
            conn_el.commit()
        conn_el.close()
        
    print(f"  -> Done {domain}: new length {len(new_content)}")

# 7. Safe cache purge (ONLY the 24 specific site directories)
print("Purging caches specifically for the 24 PBN sites...")
for c in configs:
    dom = c['domain']
    docroot = f"/www/wwwroot/{dom}"
    if os.path.exists(docroot):
        subprocess.run(f"rm -rf {docroot}/wp-content/cache/*", shell=True)
        subprocess.run(f"rm -rf {docroot}/wp-content/uploads/elementor/css/*", shell=True)

# 8. Purge LiteSpeed private cache and restart LiteSpeed
subprocess.run("rm -rf /usr/local/lsws/cachedata/priv/*", shell=True)
subprocess.run("/usr/local/lsws/bin/lswsctrl restart", shell=True)
print("All 24 sites clean injected and web server cache purged successfully!")


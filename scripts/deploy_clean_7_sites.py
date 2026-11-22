import paramiko
import sys

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import pymysql, re, json, subprocess

dead_domains = [
    'jilihot.live', 'fb88ac.com', '90jiliph.net', 'betso88club.net',
    'live777.me', 'tic88.to', 'bom88.biz', 'ralphlauren.ru.com',
    'bingoplus247.com', 'pwinph777.net', 'w500ph.net', 'luck9.fans',
    'masaya365.club', 'lodi646ph.net', 'luckycola7.top', 'casinoslovenija10.com',
    '1xbetph.org'
]

sites_plan = [
    {
        'idx': 8,
        'domain': 'sburlrecdept.com',
        'db': 'wp_sburlrecdept',
        'prefix': '9sapp_',
        'pid': 65,
        'net_links': [
            ('<a href="https://shadowdance.org" target="_blank" rel="noopener">shadowdance.org</a>', 'Trần'),
            ('<a href="https://smvhighschool.in" target="_blank" rel="noopener">55BMW</a>', 'Brand'),
            ('<a href="https://snow-design.com" target="_blank" rel="noopener">snow-design.com</a>', 'Trần'),
            ('<a href="https://stepl.org" target="_blank" rel="noopener">OKBET</a>', 'Brand')
        ],
        'brands_5': [
            ('<a href="https://ivibetreviews.com" target="_blank" rel="noopener">Ivibet</a>'),
            ('<a href="https://b2xbetguia.com" target="_blank" rel="noopener">B2xbet</a>'),
            ('<a href="https://megapariguia.com" target="_blank" rel="noopener">Megapari</a>'),
            ('<a href="https://freshcasinoguia.com" target="_blank" rel="noopener">Fresh Casino</a>'),
            ('<a href="https://jetcasinoguia.com" target="_blank" rel="noopener">Jet Casino</a>')
        ]
    },
    {
        'idx': 9,
        'domain': 'shadowdance.org',
        'db': 'wp_shadowdance_o',
        'prefix': 'wp_',
        'pid': 282,
        'net_links': [
            ('<a href="https://smvhighschool.in" target="_blank" rel="noopener">smvhighschool.in</a>', 'Trần'),
            ('<a href="https://snow-design.com" target="_blank" rel="noopener">SLOTVIP777</a>', 'Brand'),
            ('<a href="https://stepl.org" target="_blank" rel="noopener">stepl.org</a>', 'Trần'),
            ('<a href="https://suzanneloebl.com" target="_blank" rel="noopener">Betso88</a>', 'Brand')
        ],
        'brands_5': [
            ('<a href="https://ivibetguia.com" target="_blank" rel="noopener">Ivibet</a>'),
            ('<a href="https://b2xbetreview.com" target="_blank" rel="noopener">B2xbet</a>'),
            ('<a href="https://megaparibonusbr.com" target="_blank" rel="noopener">Megapari</a>'),
            ('<a href="https://freshcasinobonusbr.com" target="_blank" rel="noopener">Fresh Casino</a>'),
            ('<a href="https://jetcasinobonusbr.com" target="_blank" rel="noopener">Jet Casino</a>')
        ]
    },
    {
        'idx': 10,
        'domain': 'smvhighschool.in',
        'db': 'wp_smvhighschool',
        'prefix': 'wp_',
        'pid': 296,
        'net_links': [
            ('<a href="https://snow-design.com" target="_blank" rel="noopener">snow-design.com</a>', 'Trần'),
            ('<a href="https://stepl.org" target="_blank" rel="noopener">OKBET</a>', 'Brand'),
            ('<a href="https://suzanneloebl.com" target="_blank" rel="noopener">suzanneloebl.com</a>', 'Trần'),
            ('<a href="https://thaiasiatoday.com" target="_blank" rel="noopener">30JILI</a>', 'Brand')
        ],
        'brands_5': [
            ('<a href="https://ivibetreviews.com" target="_blank" rel="noopener">Ivibet</a>'),
            ('<a href="https://b2xbetbonusbr.com" target="_blank" rel="noopener">B2xbet</a>'),
            ('<a href="https://megapariguia.com" target="_blank" rel="noopener">Megapari</a>'),
            ('<a href="https://freshcasinoguia.com" target="_blank" rel="noopener">Fresh Casino</a>'),
            ('<a href="https://jetcasinoguia.com" target="_blank" rel="noopener">Jet Casino</a>')
        ]
    },
    {
        'idx': 11,
        'domain': 'snow-design.com',
        'db': 'wp_snow-design_c',
        'prefix': 'gfbtm_',
        'pid': 9,
        'net_links': [
            ('<a href="https://stepl.org" target="_blank" rel="noopener">stepl.org</a>', 'Trần'),
            ('<a href="https://suzanneloebl.com" target="_blank" rel="noopener">Betso88</a>', 'Brand'),
            ('<a href="https://thaiasiatoday.com" target="_blank" rel="noopener">thaiasiatoday.com</a>', 'Trần'),
            ('<a href="https://feshun.com" target="_blank" rel="noopener">10jili</a>', 'Brand')
        ],
        'brands_5': [
            ('<a href="https://ivibetguia.com" target="_blank" rel="noopener">Ivibet</a>'),
            ('<a href="https://b2xbetguia.com" target="_blank" rel="noopener">B2xbet</a>'),
            ('<a href="https://megaparibonusbr.com" target="_blank" rel="noopener">Megapari</a>'),
            ('<a href="https://freshcasinobonusbr.com" target="_blank" rel="noopener">Fresh Casino</a>'),
            ('<a href="https://jetcasinobonusbr.com" target="_blank" rel="noopener">Jet Casino</a>')
        ]
    },
    {
        'idx': 18,
        'domain': 'rogalevich.org',
        'db': 'wp_rogalevich_or',
        'prefix': 'wp_',
        'pid': 1696,
        'net_links': [
            ('<a href="https://j-core.biz" target="_blank" rel="noopener">j-core.biz</a>', 'Trần'),
            ('<a href="https://kvdevelopers.com" target="_blank" rel="noopener">63 Jili</a>', 'Brand'),
            ('<a href="https://benscarpage.com" target="_blank" rel="noopener">benscarpage.com</a>', 'Trần'),
            ('<a href="https://kylehendersonmusic.com" target="_blank" rel="noopener">JILI8998</a>', 'Brand')
        ],
        'brands_5': [
            ('<a href="https://ivibetreviews.com" target="_blank" rel="noopener">Ivibet</a>'),
            ('<a href="https://b2xbetreview.com" target="_blank" rel="noopener">B2xbet</a>'),
            ('<a href="https://megapariguia.com" target="_blank" rel="noopener">Megapari</a>'),
            ('<a href="https://freshcasinoguia.com" target="_blank" rel="noopener">Fresh Casino</a>'),
            ('<a href="https://jetcasinoguia.com" target="_blank" rel="noopener">Jet Casino</a>')
        ]
    },
    {
        'idx': 19,
        'domain': 'j-core.biz',
        'db': 'wp_j-core_biz',
        'prefix': 'wp_',
        'pid': 341,
        'net_links': [
            ('<a href="https://kvdevelopers.com" target="_blank" rel="noopener">kvdevelopers.com</a>', 'Trần'),
            ('<a href="https://benscarpage.com" target="_blank" rel="noopener">EEBET</a>', 'Brand'),
            ('<a href="https://kylehendersonmusic.com" target="_blank" rel="noopener">kylehendersonmusic.com</a>', 'Trần'),
            ('<a href="https://respectablyfrench.com" target="_blank" rel="noopener">10JILI</a>', 'Brand')
        ],
        'brands_5': [
            ('<a href="https://ivibetguia.com" target="_blank" rel="noopener">Ivibet</a>'),
            ('<a href="https://b2xbetbonusbr.com" target="_blank" rel="noopener">B2xbet</a>'),
            ('<a href="https://megaparibonusbr.com" target="_blank" rel="noopener">Megapari</a>'),
            ('<a href="https://freshcasinobonusbr.com" target="_blank" rel="noopener">Fresh Casino</a>'),
            ('<a href="https://jetcasinobonusbr.com" target="_blank" rel="noopener">Jet Casino</a>')
        ]
    },
    {
        'idx': 20,
        'domain': 'kvdevelopers.com',
        'db': 'wp_kvdevelopers',
        'prefix': '9sapp_',
        'pid': 554,
        'net_links': [
            ('<a href="https://benscarpage.com" target="_blank" rel="noopener">benscarpage.com</a>', 'Trần'),
            ('<a href="https://kylehendersonmusic.com" target="_blank" rel="noopener">JILI8998</a>', 'Brand'),
            ('<a href="https://respectablyfrench.com" target="_blank" rel="noopener">respectablyfrench.com</a>', 'Trần'),
            ('<a href="https://sougicocoro.com" target="_blank" rel="noopener">12BET</a>', 'Brand')
        ],
        'brands_5': [
            ('<a href="https://ivibetreviews.com" target="_blank" rel="noopener">Ivibet</a>'),
            ('<a href="https://b2xbetguia.com" target="_blank" rel="noopener">B2xbet</a>'),
            ('<a href="https://megapariguia.com" target="_blank" rel="noopener">Megapari</a>'),
            ('<a href="https://freshcasinoguia.com" target="_blank" rel="noopener">Fresh Casino</a>'),
            ('<a href="https://jetcasinoguia.com" target="_blank" rel="noopener">Jet Casino</a>')
        ]
    }
]

def clean_dead_links(html):
    def replace_link(m):
        full = m.group(0)
        href = m.group(1)
        text = m.group(2)
        for dl in dead_domains:
            if dl in href.lower():
                # unwrap link safely
                return text
        return full
    return re.sub(r'<a\\s+[^>]*href=[\"\\\']([^\"\\\']+)[\"\\\'][^>]*>(.*?)</a>', replace_link, html, flags=re.I|re.S)

for s in sites_plan:
    db = s['db']
    prefix = s['prefix']
    domain = s['domain']
    pid = s['pid']
    
    conn = pymysql.connect(host='127.0.0.1', user='root', password='dc2fe6f2608cdc00', database=db)
    cur = conn.cursor()
    
    cur.execute(f"SELECT post_content FROM {prefix}posts WHERE ID=%s", (pid,))
    row = cur.fetchone()
    content = row[0] if row else ""
    
    # 1. Clean dead links
    content = clean_dead_links(content)
    
    # 2. Build Gutenberg block HTML
    nl = [x[0] for x in s['net_links']]
    b5 = s['brands_5']
    
    section_html = f'''<!-- wp:html -->
<section class="partner-network-section" style="margin-top: 35px; padding: 25px 0; border-top: 1px solid #e2e8f0;">
    <h3>Recommended Gaming Platforms &amp; Trusted Network Partners</h3>
    <p>Discover top-rated online gaming hubs and entertainment destinations verified across the network. For direct portal access and community updates, explore {nl[0]} and {nl[1]}, or connect via {nl[2]} and {nl[3]} for official services.</p>
    <p>Looking for exclusive bonuses and comprehensive casino guides? Check out premier gaming options including {b5[0]}, {b5[1]}, {b5[2]}, {b5[3]}, and {b5[4]} for up-to-date promotional codes and mobile play.</p>
</section>
<!-- /wp:html -->'''

    # Ensure no duplicate section
    content = re.sub(r'<!-- wp:html -->\\s*<section class="partner-network-section".*?</section>\\s*<!-- /wp:html -->', '', content, flags=re.S)
    content = re.sub(r'<section class="partner-network-section".*?</section>', '', content, flags=re.S)
    
    # Append cleanly
    new_content = content.rstrip() + "\\n\\n" + section_html
    
    # Update posts table via parameterized query
    cur.execute(f"UPDATE {prefix}posts SET post_content=%s WHERE ID=%s", (new_content, pid))
    
    # For kvdevelopers.com (Elementor), also update _elementor_data
    if domain == 'kvdevelopers.com':
        cur.execute(f"SELECT meta_value FROM {prefix}postmeta WHERE post_id=%s AND meta_key='_elementor_data'", (pid,))
        elem_row = cur.fetchone()
        if elem_row:
            try:
                tree = json.loads(elem_row[0])
                # remove old widget if exists
                tree = [n for n in tree if n.get("id") != "partnernetcont"]
                elem_widget = {
                    "id": "partnernetcont",
                    "elType": "section",
                    "isInner": False,
                    "settings": {},
                    "elements": [{
                        "id": "partnernetcont_col",
                        "elType": "column",
                        "isInner": False,
                        "settings": {"_column_size": 100},
                        "elements": [{
                            "id": "partnernetcont_html",
                            "elType": "widget",
                            "widgetType": "html",
                            "settings": {"html": section_html.replace('<!-- wp:html -->', '').replace('<!-- /wp:html -->', '').strip()}
                        }]
                    }]
                }
                tree.append(elem_widget)
                cur.execute(f"UPDATE {prefix}postmeta SET meta_value=%s WHERE post_id=%s AND meta_key='_elementor_data'", (json.dumps(tree), pid))
                print(f"Updated Elementor tree for {domain}")
            except Exception as e:
                print(f"Error updating Elementor for {domain}: {e}")
                
    conn.commit()
    conn.close()
    print(f"Successfully deployed backlinks to {domain} (pid={pid})")

subprocess.run("rm -rf /usr/local/lsws/cachedata/priv/*", shell=True)
subprocess.run("/usr/local/lsws/bin/lswsctrl reload", shell=True)
print("LSWS cache cleared and reloaded.")
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)

sftp = ssh.open_sftp()
with sftp.file('/tmp/deploy_clean_7_sites.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/deploy_clean_7_sites.py')
sys.stdout.reconfigure(encoding='utf-8')
print("STDOUT:\n", stdout.read().decode('utf-8', errors='ignore'))
print("STDERR:\n", stderr.read().decode('utf-8', errors='ignore'))
ssh.close()


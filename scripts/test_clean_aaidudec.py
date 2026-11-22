import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import pymysql, re, subprocess

# 1. Restore pristine backup for aaidudec.org
subprocess.run("mysql -uroot -pdc2fe6f2608cdc00 wp_aaidudec_org < /tmp/pbn_backups/aaidudec.org_24.sql", shell=True)

# 2. Read directly via PyMySQL (NO CLI ESCAPING)
conn = pymysql.connect(host='127.0.0.1', user='root', password='dc2fe6f2608cdc00', database='wp_aaidudec_org')
cur = conn.cursor()
cur.execute("SELECT post_content FROM wp_posts WHERE ID=24")
content = cur.fetchone()[0]

# 3. Clean dead links
dead_domains = [
    "1xbetph.org", "phmacaoclub.com", "9apps.tips", "jilihot.live",
    "betso88club.net", "nice88.live", "phlove777.com", "90jilivip.bet",
    "peso888.fans", "live777.me", "bingoplus247.com", "pwinph777.net",
    "w500ph.net", "luck9.fans", "masaya365.club", "lodi646ph.net",
    "luckycola7.top", "jiliplay8888.live", "ralphlauren.ru.com", "tic88.to",
    "jiliasiabet.net"
]

def unwrap_dead_links(match):
    full_tag = match.group(0)
    href = match.group(1)
    anchor_text = match.group(2)
    for dd in dead_domains:
        if dd in href.lower():
            return anchor_text
    return full_tag

pattern = re.compile(r'<a\\s+[^>]*href=[\\\'"]([^\\\'"]+)[\\\'"][^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)
content = pattern.sub(unwrap_dead_links, content)

# 4. Append clean Gutenberg HTML block for backlinks
section_html = '''
<!-- wp:html -->
<section class="partner-network-section" style="margin-top: 35px; padding: 25px 0; border-top: 1px solid #e2e8f0;">
    <h3>Recommended Gaming Platforms &amp; Trusted Network Partners</h3>
    <p>Discover top-rated online gaming hubs and entertainment destinations verified across the network. For direct portal access and community updates, explore <a href="https://anthonyruivivar.net" target="_blank" rel="noopener">anthonyruivivar.net</a> and <a href="https://bblatinamerica.com" target="_blank" rel="noopener">BET88</a>, or connect via <a href="https://conadecivil.com" target="_blank" rel="noopener">conadecivil.com</a> and <a href="https://facturatabasco.com" target="_blank" rel="noopener">PHmacao</a> for official services.</p>
    <p>Looking for exclusive bonuses and comprehensive casino guides? Check out premier gaming options including <a href="https://ivibetguia.com" target="_blank" rel="noopener">Ivibet</a>, <a href="https://b2xbetbonusbr.com" target="_blank" rel="noopener">B2xbet</a>, <a href="https://megaparibonusbr.com" target="_blank" rel="noopener">Megapari</a>, <a href="https://freshcasinobonusbr.com" target="_blank" rel="noopener">Fresh Casino</a>, and <a href="https://jetcasinobonusbr.com" target="_blank" rel="noopener">Jet Casino</a> for up-to-date promotional codes and mobile play.</p>
</section>
<!-- /wp:html -->
'''

new_content = content.strip() + "\\n\\n" + section_html.strip() + "\\n"
cur.execute("UPDATE wp_posts SET post_content=%s WHERE ID=24", (new_content,))
conn.commit()
conn.close()

# 5. Clear cache & reload OLS
subprocess.run("rm -rf /www/wwwroot/aaidudec.org/wp-content/cache/*", shell=True)
subprocess.run("rm -rf /usr/local/lsws/cachedata/priv/*", shell=True)
subprocess.run("/usr/local/lsws/bin/lswsctrl reload", shell=True)
print("SUCCESS on aaidudec.org")
"""

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
    
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/test_clean_aaidudec.py', 'w') as f:
        f.write(remote_code)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command('python3 /tmp/test_clean_aaidudec.py')
    print(stdout.read().decode('utf-8'))
    print(stderr.read().decode('utf-8'))
    ssh.close()

if __name__ == "__main__":
    main()


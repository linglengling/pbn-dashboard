import paramiko

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = """
import pymysql, json, re, subprocess

db = "wp_kvdevelopers"
prefix = "9sapp_"
pid = 554

conn = pymysql.connect(host="127.0.0.1", user="root", password="dc2fe6f2608cdc00", database=db)
cur = conn.cursor()

cur.execute(f"SELECT meta_value FROM {prefix}postmeta WHERE post_id={pid} AND meta_key='_elementor_data'")
row = cur.fetchone()
elem_tree = json.loads(row[0])

# Clean dead links recursively
dead_links = ["lodi646ph.net", "luckycola7.top", "1xbetph.org", "casinoslovenija10.com"]

def clean_node(node):
    if isinstance(node, dict):
        for k, v in list(node.items()):
            if isinstance(v, str):
                for dl in dead_links:
                    if dl in v.lower():
                        node[k] = re.sub(r'https?://[^\\s\"\\\'><]*' + re.escape(dl) + r'[^\\s\"\\\'><]*', '#', v, flags=re.I)
            else:
                clean_node(v)
    elif isinstance(node, list):
        for item in node:
            clean_node(item)

clean_node(elem_tree)

# Remove existing partnernetcont if any
elem_tree = [n for n in elem_tree if n.get("id") != "partnernetcont"]

# Generate Section HTML for kvdevelopers.com (STT 20)
net_l1 = '<a href="https://benscarpage.com" target="_blank" rel="noopener">benscarpage.com</a>'
net_l2 = '<a href="https://kylehendersonmusic.com" target="_blank" rel="noopener">JILI8998</a>'
net_l3 = '<a href="https://respectablyfrench.com" target="_blank" rel="noopener">respectablyfrench.com</a>'
net_l4 = '<a href="https://sougicocoro.com" target="_blank" rel="noopener">12BET</a>'

b_l1 = '<a href="https://ivibetreviews.com" target="_blank" rel="noopener">Ivibet</a>'
b_l2 = '<a href="https://b2xbetguia.com" target="_blank" rel="noopener">B2xbet</a>'
b_l3 = '<a href="https://megapariguia.com" target="_blank" rel="noopener">Megapari</a>'
b_l4 = '<a href="https://freshcasinoguia.com" target="_blank" rel="noopener">Fresh Casino</a>'
b_l5 = '<a href="https://jetcasinoguia.com" target="_blank" rel="noopener">Jet Casino</a>'

section_html = f'''
<section class="partner-network-section" style="margin-top: 35px; padding: 25px 0; border-top: 1px solid #e2e8f0;">
    <h3>Recommended Gaming Platforms &amp; Trusted Network Partners</h3>
    <p>Discover top-rated online gaming hubs and entertainment destinations verified across the network. For direct portal access and community updates, explore {net_l1} and {net_l2}, or connect via {net_l3} and {net_l4} for official services.</p>
    <p>Looking for exclusive bonuses and comprehensive casino guides? Check out premier gaming options including {b_l1}, {b_l2}, {b_l3}, {b_l4}, and {b_l5} for up-to-date promotional codes and mobile play.</p>
</section>
'''

new_node = {
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
}

elem_tree.append(new_node)
new_json = json.dumps(elem_tree)

cur.execute(f"UPDATE {prefix}postmeta SET meta_value=%s WHERE post_id={pid} AND meta_key='_elementor_data'", (new_json,))
conn.commit()
conn.close()
print("Successfully updated Elementor data for kvdevelopers.com!")

# Clear cache
subprocess.run("rm -rf /www/wwwroot/kvdevelopers.com/wp-content/uploads/elementor/css/*", shell=True)
subprocess.run("rm -rf /www/wwwroot/kvdevelopers.com/wp-content/cache/*", shell=True)
subprocess.run("rm -rf /usr/local/lsws/cachedata/priv/*", shell=True)
subprocess.run("/usr/local/lsws/bin/lswsctrl reload", shell=True)
print("Cleared cache and reloaded OLS!")
"""

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
    
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/update_elem_kv.py', 'w') as f:
        f.write(remote_code)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command('python3 /tmp/update_elem_kv.py')
    print(stdout.read().decode('utf-8'))
    print(stderr.read().decode('utf-8'))
    ssh.close()

if __name__ == "__main__":
    main()

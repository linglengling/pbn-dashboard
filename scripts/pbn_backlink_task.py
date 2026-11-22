import paramiko
import json

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_script_lines = [
    "import subprocess, json, re, urllib.request, socket",
    "socket.setdefaulttimeout(3)",
    "",
    "sites = [",
    "    ('aaidudec.org', 'wp_aaidudec_org', 24),",
    "    ('anthonyruivivar.net', 'wp_anthonyruiviv', 2109),",
    "    ('bblatinamerica.com', 'wp_bblatinameric', 1696),",
    "    ('conadecivil.com', 'wp_conadecivil_c', 9),",
    "    ('facturatabasco.com', 'wp_facturatabasc', 65),",
    "    ('greatdrivingchallenge.com', 'wp_greatdrivingc', 20253),",
    "    ('hkhoe.com', 'wp_hkhoe_com', 9),",
    "    ('sburlrecdept.com', 'wp_sburlrecdept', 65),",
    "    ('shadowdance.org', 'wp_shadowdance_o', 282),",
    "    ('smvhighschool.in', 'wp_smvhighschool', 296),",
    "    ('snow-design.com', 'wp_snow-design_c', 9),",
    "    ('stepl.org', 'wp_stepl_org', 9),",
    "    ('suzanneloebl.com', 'wp_suzanneloebl', 11),",
    "    ('thaiasiatoday.com', 'wp_thaiasiatoday', 25),",
    "    ('feshun.com', 'wp_feshun_com', 65),",
    "    ('hellbenderpress.com', 'wp_hellbenderpre', 21),",
    "    ('innkeeperrockies.com', 'wp_innkeeperrock', 9),",
    "    ('rogalevich.org', 'wp_rogalevich_or', 1696),",
    "    ('j-core.biz', 'wp_j-core_biz', 341),",
    "    ('kvdevelopers.com', 'wp_kvdevelopers', 554),",
    "    ('benscarpage.com', 'wp_benscarpage_c', 11),",
    "    ('kylehendersonmusic.com', 'wp_kylehenderson', 85),",
    "    ('respectablyfrench.com', 'wp_respectablyfr', 11),",
    "    ('sougicocoro.com', 'wp_sougicocoro_c', 3040)",
    "]",
    "",
    "results = []",
    "for domain, dbname, pid in sites:",
    "    cmd = ['mysql', '-uroot', '-pdc2fe6f2608cdc00', dbname, '-N', '-s', '-e', f'SELECT post_content FROM wp_posts WHERE ID={pid}']",
    "    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors='ignore')",
    "    content = p.stdout",
    "    pattern = re.compile(r'<a\\s+[^>]*href=[\"\\\']([^\"\\\']+)[\"\\\'][^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)",
    "    a_tags = pattern.findall(content)",
    "    ext_links = []",
    "    for href, text in a_tags:",
    "        clean_text = re.sub(r'<[^>]+>', '', text).strip()",
    "        if domain not in href and href.startswith('http'):",
    "            ext_links.append({'href': href, 'anchor': clean_text})",
    "    results.append({",
    "        'domain': domain,",
    "        'db': dbname,",
    "        'pid': pid,",
    "        'content_len': len(content),",
    "        'ext_links': ext_links",
    "    })",
    "",
    "print(json.dumps(results, ensure_ascii=False, indent=2))"
]

remote_code = "\n".join(remote_script_lines)

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
    
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/inspect_pbn_sites.py', 'w') as f:
        f.write(remote_code)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command('python3 /tmp/inspect_pbn_sites.py')
    out = stdout.read().decode('utf-8')
    err = stderr.read().decode('utf-8')
    
    if err:
        print("STDERR:", err)
    
    with open("scripts_inspect_out.json", "w", encoding="utf-8") as f:
        f.write(out)
    print("Done. Output written to scripts_inspect_out.json")
    ssh.close()

if __name__ == "__main__":
    main()

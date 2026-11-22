import paramiko
import json

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_script_lines = [
    "import os, re, json, subprocess, socket, urllib.request",
    "from concurrent.futures import ThreadPoolExecutor",
    "",
    "with open('/tmp/site_configs.json', 'r') as f:",
    "    configs = json.load(f)",
    "",
    "# 1. Backup posts table for all 24 sites",
    "backup_dir = '/tmp/pbn_backups'",
    "os.makedirs(backup_dir, exist_ok=True)",
    "for c in configs:",
    "    db = c['db_name']",
    "    prefix = c['prefix']",
    "    pid = c['page_on_front']",
    "    backup_file = f\"{backup_dir}/{c['domain']}_{pid}.sql\"",
    "    subprocess.run(f\"mysqldump -uroot -pdc2fe6f2608cdc00 {db} {prefix}posts --where='ID={pid}' > {backup_file}\", shell=True)",
    "print('Backup completed.')",
    "",
    "# 2. Extract all external links from page_on_front content",
    "all_ext_links = []",
    "for c in configs:",
    "    db = c['db_name']",
    "    prefix = c['prefix']",
    "    pid = c['page_on_front']",
    "    domain = c['domain']",
    "    ",
    "    p = subprocess.run(['mysql', '-uroot', '-pdc2fe6f2608cdc00', db, '-N', '-s', '-e',",
    "                        f\"SELECT post_content FROM {prefix}posts WHERE ID={pid}\"],",
    "                       stdout=subprocess.PIPE, text=True, errors='ignore')",
    "    content = p.stdout",
    "    pattern = re.compile(r'<a\\s+[^>]*href=[\"\\\']([^\"\\\']+)[\"\\\'][^>]*>(.*?)</a>', re.I | re.S)",
    "    for href, text in pattern.findall(content):",
    "        clean_text = re.sub(r'<[^>]+>', '', text).strip()",
    "        if href.startswith('http') and domain not in href:",
    "            all_ext_links.append({",
    "                'src_domain': domain,",
    "                'href': href,",
    "                'anchor': clean_text",
    "            })",
    "",
    "print(f'Total external links found: {len(all_ext_links)}')",
    "",
    "# 3. Test external links for DNS & HTTP connectivity",
    "def check_url(item):",
    "    url = item['href']",
    "    status = 'unknown'",
    "    # extract host",
    "    m = re.match(r'https?://([^/:]+)', url)",
    "    if not m:",
    "        return dict(item, status='invalid_url')",
    "    host = m.group(1)",
    "    try:",
    "        socket.gethostbyname(host)",
    "    except Exception as e:",
    "        return dict(item, status='dns_dead', error=str(e))",
    "    ",
    "    # Test HTTP request",
    "    try:",
    "        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})",
    "        with urllib.request.urlopen(req, timeout=3) as resp:",
    "            return dict(item, status='alive', code=resp.status)",
    "    except urllib.error.HTTPError as e:",
    "        return dict(item, status=f'http_{e.code}', code=e.code)",
    "    except Exception as e:",
    "        return dict(item, status='request_failed', error=str(e))",
    "",
    "with ThreadPoolExecutor(max_workers=20) as executor:",
    "    audit_results = list(executor.map(check_url, all_ext_links))",
    "",
    "with open('/tmp/dead_links_audit.json', 'w') as f:",
    "    json.dump(audit_results, f, ensure_ascii=False, indent=2)",
    "",
    "# Summary of dead links",
    "dead_links = [r for r in audit_results if r['status'] in ('dns_dead', 'invalid_url') or str(r.get('status','')).startswith('http_4') or str(r.get('status','')).startswith('http_5') or '1xbetph.org' in r['href']]",
    "print(f'Total dead/suspicious links: {len(dead_links)}')",
    "for dl in dead_links:",
    "    print(f\"  [{dl['src_domain']}] -> {dl['href']} ({dl['anchor']}) : {dl['status']}\")",
]

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
    
    # Upload site_configs.json to /tmp/site_configs.json
    sftp = ssh.open_sftp()
    sftp.put("site_configs.json", "/tmp/site_configs.json")
    with sftp.file('/tmp/audit_and_backup.py', 'w') as f:
        f.write("\n".join(remote_script_lines))
    sftp.close()
    
    print("Running audit and backup on VPS...")
    stdin, stdout, stderr = ssh.exec_command('python3 /tmp/audit_and_backup.py')
    print(stdout.read().decode('utf-8'))
    print(stderr.read().decode('utf-8'))
    
    # Download dead_links_audit.json
    sftp = ssh.open_sftp()
    sftp.get("/tmp/dead_links_audit.json", "dead_links_audit.json")
    sftp.close()
    print("Downloaded dead_links_audit.json")
    ssh.close()

if __name__ == "__main__":
    main()


import paramiko
import json

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_script_lines = [
    "import os, re, json, subprocess",
    "",
    "domains = [",
    "    'aaidudec.org', 'anthonyruivivar.net', 'bblatinamerica.com', 'conadecivil.com',",
    "    'facturatabasco.com', 'greatdrivingchallenge.com', 'hkhoe.com', 'sburlrecdept.com',",
    "    'shadowdance.org', 'smvhighschool.in', 'snow-design.com', 'stepl.org',",
    "    'suzanneloebl.com', 'thaiasiatoday.com', 'feshun.com', 'hellbenderpress.com',",
    "    'innkeeperrockies.com', 'rogalevich.org', 'j-core.biz', 'kvdevelopers.com',",
    "    'benscarpage.com', 'kylehendersonmusic.com', 'respectablyfrench.com', 'sougicocoro.com'",
    "]",
    "",
    "site_configs = []",
    "for domain in domains:",
    "    wp_config = f'/www/wwwroot/{domain}/wp-config.php'",
    "    if not os.path.exists(wp_config):",
    "        site_configs.append({'domain': domain, 'error': 'wp-config.php not found'})",
    "        continue",
    "    ",
    "    with open(wp_config, 'r', errors='ignore') as f:",
    "        content = f.read()",
    "    ",
    "    prefix_match = re.search(r\"\\$table_prefix\\s*=\\s*['\\\"]([^'\\\"]+)['\\\"]\", content)",
    "    prefix = prefix_match.group(1) if prefix_match else 'wp_'",
    "    ",
    "    db_name_m = re.search(r\"define\\(\\s*['\\\"]DB_NAME['\\\"]\\s*,\\s*['\\\"]([^'\\\"]+)['\\\"]\\s*\\)\", content)",
    "    db_name = db_name_m.group(1) if db_name_m else ''",
    "    ",
    "    # Get show_on_front and page_on_front",
    "    cmd = ['mysql', '-uroot', '-pdc2fe6f2608cdc00', db_name, '-N', '-s', '-e',",
    "           f\"SELECT option_name, option_value FROM {prefix}options WHERE option_name IN ('show_on_front', 'page_on_front', 'siteurl')\"]",
    "    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)",
    "    opts = dict([line.split('\\t') for line in p.stdout.strip().split('\\n') if '\\t' in line])",
    "    ",
    "    pid = int(opts.get('page_on_front', 0))",
    "    ",
    "    # Get post_content length & title",
    "    cmd2 = ['mysql', '-uroot', '-pdc2fe6f2608cdc00', db_name, '-N', '-s', '-e',",
    "            f\"SELECT ID, post_title, LENGTH(post_content) FROM {prefix}posts WHERE ID={pid}\"]",
    "    p2 = subprocess.run(cmd2, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)",
    "    post_info = p2.stdout.strip().split('\\t') if p2.stdout.strip() else []",
    "    ",
    "    # Check menus via wp cli",
    "    cmd_menu = f\"wp --allow-root --path=/www/wwwroot/{domain} menu location list --format=json\"",
    "    p_menu = subprocess.run(cmd_menu, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)",
    "    menu_loc = p_menu.stdout.strip()",
    "    ",
    "    site_configs.append({",
    "        'domain': domain,",
    "        'db_name': db_name,",
    "        'prefix': prefix,",
    "        'siteurl': opts.get('siteurl', ''),",
    "        'page_on_front': pid,",
    "        'post_title': post_info[1] if len(post_info) > 1 else '',",
    "        'content_len': int(post_info[2]) if len(post_info) > 2 else 0,",
    "        'menu_loc': menu_loc",
    "    })",
    "",
    "print(json.dumps(site_configs, ensure_ascii=False, indent=2))"
]

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
    
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/get_full_configs.py', 'w') as f:
        f.write("\n".join(remote_script_lines))
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command('python3 /tmp/get_full_configs.py')
    out = stdout.read().decode('utf-8')
    with open("site_configs.json", "w", encoding="utf-8") as f:
        f.write(out)
    print("Done. Saved to site_configs.json")
    ssh.close()

if __name__ == "__main__":
    main()


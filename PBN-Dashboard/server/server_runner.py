import os
import sys
import json
import sqlite3
import paramiko

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = os.path.join(os.path.dirname(__file__), 'pbn_matrix.db')
PLUGIN_CANDIDATES = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), 'pbn-manager.php')),
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'mu-plugins', 'pbn-manager.php')),
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'mu-plugins', 'pbn-manager.php')),
    os.path.abspath('/www/wwwroot/phn-manage.sites/mu-plugins/pbn-manager.php'),
    os.path.abspath('/www/wwwroot/phn-manage.sites/server/pbn-manager.php')
]
PLUGIN_PATH = next((p for p in PLUGIN_CANDIDATES if os.path.exists(p)), PLUGIN_CANDIDATES[0])

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def connect_ssh(server, timeout=10):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    host = server['host']
    port = int(server.get('port') or 22)
    user = server['username']
    pw = server['password']
    ssh.connect(host, port=port, username=user, password=pw, timeout=timeout, banner_timeout=timeout)
    return ssh

def test_server(server):
    try:
        ssh = connect_ssh(server, timeout=8)
        stdin, stdout, stderr = ssh.exec_command('hostname; whoami')
        info = stdout.read().decode('utf-8', errors='ignore').strip().replace('\n', ' | ')
        
        # Quick count of WP sites
        if server['type'] == 'vps':
            cmd = "find /www/wwwroot -maxdepth 3 -name 'wp-config.php' 2>/dev/null | wc -l"
        else:
            cmd = "find ~ -maxdepth 4 -name 'wp-config.php' ! -path '*/.trash/*' ! -path '*/wordpress-backups/*' 2>/dev/null | wc -l"
            
        stdin, stdout, stderr = ssh.exec_command(cmd)
        count_str = stdout.read().decode('utf-8', errors='ignore').strip()
        count = int(count_str) if count_str.isdigit() else 0
        ssh.close()
        return {"success": True, "info": info, "sites_count": count}
    except Exception as e:
        return {"success": False, "error": str(e)}

def scan_server_sites(server):
    try:
        ssh = connect_ssh(server, timeout=12)
        stype = server['type']
        host = server['host']
        server_id = server.get('id')
        
        sites = []
        if stype == 'vps':
            cmd = "find /www/wwwroot -maxdepth 3 -name 'wp-config.php' 2>/dev/null"
            stdin, stdout, stderr = ssh.exec_command(cmd)
            cfgs = stdout.read().decode('utf-8', errors='ignore').strip().splitlines()
            for cfg in cfgs:
                if not cfg.strip():
                    continue
                site_dir = os.path.dirname(cfg)
                domain = os.path.basename(site_dir)
                # Some sites might be in subfolders like bayvip.life/bayvip.life
                if domain.startswith('.'):
                    continue
                site_url = f"https://{domain}"
                sites.append({
                    "domain": domain,
                    "site_url": site_url,
                    "server_host": host,
                    "server_id": server_id,
                    "server_ip": host,
                    "path": site_dir
                })
        else:
            # cPanel: Get addon domains from uapi if possible, plus directory scan
            domain_map = {}
            try:
                stdin, stdout, stderr = ssh.exec_command("uapi DomainInfo list_domains --output=json 2>/dev/null")
                uapi_out = stdout.read().decode('utf-8', errors='ignore')
                uapi_data = json.loads(uapi_out)
                addon_list = uapi_data.get('result', {}).get('data', {}).get('addon_domains', [])
                main_dom = uapi_data.get('result', {}).get('data', {}).get('main_domain', '')
                if main_dom:
                    domain_map[main_dom.replace('.', '')] = main_dom
                for d in addon_list:
                    domain_map[d.replace('.', '')] = d
            except Exception:
                pass

            cmd = "find ~ -maxdepth 4 -name 'wp-config.php' ! -path '*/.trash/*' ! -path '*/wordpress-backups/*' 2>/dev/null"
            stdin, stdout, stderr = ssh.exec_command(cmd)
            cfgs = stdout.read().decode('utf-8', errors='ignore').strip().splitlines()
            for cfg in cfgs:
                if not cfg.strip():
                    continue
                site_dir = os.path.dirname(cfg)
                folder_name = os.path.basename(site_dir)
                
                # Resolve real domain from map or folder name
                domain = domain_map.get(folder_name)
                if not domain:
                    # If folder name has dots, e.g. tructiep3s.app
                    if '.' in folder_name:
                        domain = folder_name
                    else:
                        domain = folder_name
                
                site_url = f"https://{domain}"
                sites.append({
                    "domain": domain,
                    "site_url": site_url,
                    "server_host": host,
                    "server_id": server_id,
                    "server_ip": host,
                    "path": site_dir
                })
                
        ssh.close()
        return {"success": True, "sites": sites, "count": len(sites)}
    except Exception as e:
        return {"success": False, "error": str(e), "sites": []}

def deploy_to_server(server, plugin_file=PLUGIN_PATH):
    if not os.path.exists(plugin_file):
        return {"success": False, "error": f"Plugin file not found at {plugin_file}"}
        
    stype = server['type']
    host = server['host']
    user = server['username']
    print(f"[{server.get('name', host)}] Starting deployment...", flush=True)
    
    try:
        ssh = connect_ssh(server, timeout=12)
        sftp = ssh.open_sftp()
        
        if stype == 'vps':
            remote_tmp = "/tmp/pbn-manager.php"
            sftp.put(plugin_file, remote_tmp)
            sftp.close()
            
            bash_cmd = """
            count=0
            for cfg in $(find /www/wwwroot -maxdepth 3 -name 'wp-config.php' 2>/dev/null); do
                site_dir=$(dirname "$cfg")
                mu_dir="$site_dir/wp-content/mu-plugins"
                mkdir -p "$mu_dir"
                cp /tmp/pbn-manager.php "$mu_dir/pbn-manager.php"
                chmod 644 "$mu_dir/pbn-manager.php"
                chown -R www:www "$mu_dir" 2>/dev/null || true
                count=$((count+1))
            done
            rm -f /tmp/pbn-manager.php
            echo "DEPLOYED_COUNT=$count"
            """
        else:
            remote_tmp = "pbn-manager.tmp"
            sftp.put(plugin_file, remote_tmp)
            sftp.close()
            
            bash_cmd = """
            count=0
            for cfg in $(find ~ -maxdepth 4 -name 'wp-config.php' ! -path '*/.trash/*' ! -path '*/wordpress-backups/*' 2>/dev/null); do
                site_dir=$(dirname "$cfg")
                mu_dir="$site_dir/wp-content/mu-plugins"
                mkdir -p "$mu_dir"
                cp ~/pbn-manager.tmp "$mu_dir/pbn-manager.php"
                chmod 644 "$mu_dir/pbn-manager.php"
                count=$((count+1))
            done
            rm -f ~/pbn-manager.tmp
            echo "DEPLOYED_COUNT=$count"
            """
            
        stdin, stdout, stderr = ssh.exec_command(bash_cmd)
        out = stdout.read().decode('utf-8', errors='ignore').strip()
        ssh.close()
        
        count = 0
        for line in out.splitlines():
            if "DEPLOYED_COUNT=" in line:
                try:
                    count = int(line.split('=')[1].strip())
                except:
                    pass
                    
        print(f"[{server.get('name', host)}] Success: {count} sites deployed", flush=True)
        return {"success": True, "count": count, "output": out}
    except Exception as e:
        print(f"[{server.get('name', host)}] Error: {e}", flush=True)
        return {"success": False, "error": str(e), "count": 0}

def sync_sites_to_db(sites):
    if not sites:
        return 0
    conn = get_db()
    cur = conn.cursor()
    imported = 0
    for s in sites:
        domain = s['domain'].strip().lower()
        if not domain:
            continue
        cur.execute("""
            INSERT INTO sites (domain, site_url, server_host, server_id, server_ip, approval_status, status, cluster)
            VALUES (?, ?, ?, ?, ?, 'APPROVED', 'ONLINE', 'default')
            ON CONFLICT(domain) DO UPDATE SET
                site_url = COALESCE(excluded.site_url, sites.site_url),
                server_host = excluded.server_host,
                server_id = excluded.server_id,
                server_ip = COALESCE(excluded.server_ip, sites.server_ip),
                approval_status = 'APPROVED'
        """, (domain, s['site_url'], s['server_host'], s.get('server_id'), s['server_ip']))
        imported += 1
    conn.commit()
    conn.close()
    return imported

if __name__ == '__main__':
    action = sys.argv[1] if len(sys.argv) > 1 else 'help'
    
    if action == 'test_all':
        conn = get_db()
        servers = conn.execute("SELECT * FROM servers").fetchall()
        results = []
        for s in servers:
            s_dict = dict(s)
            res = test_server(s_dict)
            status = 'ONLINE' if res['success'] else 'ERROR'
            sites_count = res.get('sites_count', 0)
            conn.execute("""
                UPDATE servers 
                SET status = ?, sites_count = ?, last_checked = datetime('now','localtime'), error_message = ?
                WHERE id = ?
            """, (status, sites_count, res.get('error'), s_dict['id']))
            conn.commit()
            results.append({"server": s_dict['name'], "status": status, "sites_count": sites_count})
        conn.close()
        print(json.dumps(results, ensure_ascii=False, indent=2))

    elif action == 'scan_and_sync_all':
        conn = get_db()
        servers = conn.execute("SELECT * FROM servers").fetchall()
        total_sites = 0
        for s in servers:
            s_dict = dict(s)
            print(f"Scanning {s_dict['name']} ({s_dict['host']})...", flush=True)
            res = scan_server_sites(s_dict)
            if res['success']:
                count = sync_sites_to_db(res['sites'])
                conn.execute("""
                    UPDATE servers 
                    SET sites_count = ?, status = 'ONLINE', last_checked = datetime('now','localtime')
                    WHERE id = ?
                """, (count, s_dict['id']))
                conn.commit()
                print(f"  -> Discovered & Synced {count} sites", flush=True)
                total_sites += count
            else:
                print(f"  -> Scan failed: {res.get('error')}", flush=True)
        conn.close()
        print(f"TOTAL SITES SYNCED ACROSS ALL SERVERS: {total_sites}")

    elif action == 'deploy_all':
        conn = get_db()
        servers = conn.execute("SELECT * FROM servers").fetchall()
        total_deployed = 0
        for s in servers:
            s_dict = dict(s)
            res = deploy_to_server(s_dict)
            if res['success']:
                total_deployed += res['count']
                conn.execute("""
                    UPDATE servers 
                    SET sites_count = ?, status = 'ONLINE', last_checked = datetime('now','localtime')
                    WHERE id = ?
                """, (res['count'], s_dict['id']))
                conn.commit()
        conn.close()
        print(f"TOTAL SITES DEPLOYED: {total_deployed}")

    elif action == 'single':
        # Single server action: python server_runner.py single <sub_action> <server_id>
        sub_action = sys.argv[2]
        server_id = int(sys.argv[3])
        conn = get_db()
        row = conn.execute("SELECT * FROM servers WHERE id = ?", (server_id,)).fetchone()
        conn.close()
        if not row:
            print(json.dumps({"success": False, "error": "Server not found"}))
            sys.exit(1)
        s_dict = dict(row)
        
        if sub_action == 'test':
            res = test_server(s_dict)
            status = 'ONLINE' if res['success'] else 'ERROR'
            conn = get_db()
            conn.execute("UPDATE servers SET status = ?, sites_count = ?, last_checked = datetime('now','localtime'), error_message = ? WHERE id = ?",
                         (status, res.get('sites_count', 0), res.get('error'), server_id))
            conn.commit()
            conn.close()
            print(json.dumps(res, ensure_ascii=False))
        elif sub_action == 'scan':
            res = scan_server_sites(s_dict)
            if res['success']:
                count = sync_sites_to_db(res['sites'])
                conn = get_db()
                conn.execute("UPDATE servers SET sites_count = ?, status = 'ONLINE', last_checked = datetime('now','localtime') WHERE id = ?",
                             (count, server_id))
                conn.commit()
                conn.close()
                res['synced_count'] = count
            print(json.dumps(res, ensure_ascii=False))
        elif sub_action == 'deploy':
            res = deploy_to_server(s_dict)
            if res['success']:
                conn = get_db()
                conn.execute("UPDATE servers SET sites_count = ?, status = 'ONLINE', last_checked = datetime('now','localtime') WHERE id = ?",
                             (res['count'], server_id))
                conn.commit()
                conn.close()
            print(json.dumps(res, ensure_ascii=False))

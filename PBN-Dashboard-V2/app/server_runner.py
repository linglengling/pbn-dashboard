import os
import sys
import json
import datetime
import paramiko
from typing import Optional, List, Dict, Any

from .config import DB_PATH, PLUGIN_FILE
from .database import get_db

def connect_ssh(server: dict, timeout: int = 10):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    host = server['host']
    port = int(server.get('port') or 22)
    user = server['username']
    pw = server['password']
    ssh.connect(host, port=port, username=user, password=pw, timeout=timeout, banner_timeout=timeout)
    return ssh

def test_server(server: dict) -> dict:
    try:
        ssh = connect_ssh(server, timeout=8)
        stdin, stdout, stderr = ssh.exec_command('hostname; whoami')
        info = stdout.read().decode('utf-8', errors='ignore').strip().replace('\n', ' | ')
        
        if server['type'] == 'vps':
            cmd = "find /www/wwwroot -mindepth 2 -maxdepth 2 -name 'wp-config.php' 2>/dev/null | grep -v '\\.lo/' | wc -l"
        else:
            cmd = "find ~ -maxdepth 4 -name 'wp-config.php' ! -path '*/.trash/*' ! -path '*/wordpress-backups/*' 2>/dev/null | wc -l"
            
        stdin, stdout, stderr = ssh.exec_command(cmd)
        count_str = stdout.read().decode('utf-8', errors='ignore').strip()
        count = int(count_str) if count_str.isdigit() else 0
        ssh.close()
        return {"success": True, "info": info, "sites_count": count}
    except Exception as e:
        return {"success": False, "error": str(e)}

def scan_server_sites(server: dict) -> dict:
    try:
        ssh = connect_ssh(server, timeout=12)
        stype = server['type']
        host = server['host']
        server_id = server.get('id')
        
        sites = []
        if stype == 'vps':
            cmd = "find /www/wwwroot -mindepth 2 -maxdepth 2 -name 'wp-config.php' 2>/dev/null"
            stdin, stdout, stderr = ssh.exec_command(cmd)
            cfgs = stdout.read().decode('utf-8', errors='ignore').strip().splitlines()
            for cfg in cfgs:
                if not cfg.strip():
                    continue
                site_dir = os.path.dirname(cfg)
                domain = os.path.basename(site_dir)
                if domain.startswith('.') or domain.endswith('.lo') or domain in ['bk', 'backup', 'backups', 'temp', 'tmp'] or '.' not in domain:
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
                domain = domain_map.get(folder_name) or folder_name
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

def deploy_to_server(server: dict, plugin_file: str = PLUGIN_FILE) -> dict:
    if not os.path.exists(plugin_file):
        return {"success": False, "error": f"Plugin file not found at {plugin_file}"}
        
    stype = server['type']
    host = server['host']
    
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
        out = stdout.read().decode('utf-8', errors='ignore')
        ssh.close()
        
        count = 0
        for line in out.splitlines():
            if 'DEPLOYED_COUNT=' in line:
                try:
                    count = int(line.split('=')[1].strip())
                except:
                    pass
                    
        return {"success": True, "count": count, "message": f"Deployed mu-plugin to {count} sites"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def is_valid_domain_format(d: str) -> bool:
    if not d or not isinstance(d, str):
        return False
    d = d.strip().lower()
    if ' ' in d or '/' in d or '\\' in d or ':' in d or '@' in d:
        return False
    parts = d.split('.')
    if len(parts) < 2:
        return False
    if not parts[0] or not parts[-1]:
        return False
    if len(parts[-1]) < 2 or not parts[-1].isalpha():
        return False
    return True

def sync_scanned_sites(server: dict, sites: list) -> int:
    import urllib.parse
    with get_db() as conn:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        synced = 0
        valid_sites_count = 0
        for s in sites:
            domain = s.get('domain', '').strip().lower()
            if not is_valid_domain_format(domain):
                continue
            valid_sites_count += 1
            site_url = s.get('site_url') or f"http://{domain}"
            server_id = server['id']
            server_host = server['host']
            
            redirect_to = s.get('redirect_to')
            if not redirect_to and site_url:
                parsed_netloc = urllib.parse.urlparse(site_url).netloc.replace('www.', '').lower()
                clean_domain = domain.replace('www.', '').lower()
                if parsed_netloc and parsed_netloc != clean_domain:
                    redirect_to = site_url
            
            row = conn.execute("SELECT domain FROM sites WHERE domain = ?", (domain,)).fetchone()
            if row:
                conn.execute("""
                    UPDATE sites SET 
                        server_id = ?, server_host = ?, status = 'ONLINE', 
                        approval_status = 'APPROVED',
                        redirect_to = COALESCE(?, redirect_to), last_seen = ?
                    WHERE domain = ?
                """, (server_id, server_host, redirect_to, now, domain))
            else:
                conn.execute("""
                    INSERT INTO sites (domain, cluster, site_url, status, server_id, server_host, redirect_to, approval_status, created_at)
                    VALUES (?, ?, ?, 'ONLINE', ?, ?, ?, 'APPROVED', ?)
                """, (domain, server.get('name', server_host), site_url, server_id, server_host, redirect_to, now))
                synced += 1
                
        conn.execute("UPDATE servers SET sites_count = ?, last_checked = ?, status = 'ONLINE', error_message = NULL WHERE id = ?", (valid_sites_count, now, server['id']))
        conn.commit()
        return synced

def run_remote_cron(server: dict) -> dict:
    """Executes auto_scan_sites.py remotely via SSH and returns execution log"""
    try:
        ssh = connect_ssh(server, timeout=15)
        cmd = """
        if [ -f /www/wwwroot/pbn-tool/auto_scan_sites.py ]; then
            python3 /www/wwwroot/pbn-tool/auto_scan_sites.py
        elif [ -f ~/pbn-tool/auto_scan_sites.py ]; then
            python3 ~/pbn-tool/auto_scan_sites.py
        else
            echo "[!] Khong tim thay script /www/wwwroot/pbn-tool/auto_scan_sites.py tren may con."
            echo "[*] Vui long cai dat pbn-tool theo huong dan tren Dashboard."
        fi
        """
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
        output = stdout.read().decode('utf-8', errors='ignore')
        err = stderr.read().decode('utf-8', errors='ignore')
        ssh.close()
        full_out = (output.strip() + "\n" + (f"Errors:\n{err.strip()}" if err.strip() else "")).strip()
        return {"success": True, "output": full_out or "Da thuc thi thanh cong (khong co output)."}
    except Exception as e:
        return {"success": False, "error": str(e)}

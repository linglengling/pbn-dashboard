import os
import re
import json
import base64
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from .database import get_db, get_all_servers, get_server_by_id
from .server_runner import connect_ssh
from .cloudflare_service import resolve_domain_via_cf

def clean_domain(raw: str) -> str:
    """Normalize input domain string (remove http://, https://, paths, www., whitespace)"""
    if not raw:
        return ""
    d = raw.strip()
    if "://" not in d:
        d = "http://" + d
    try:
        parsed = urllib.parse.urlparse(d)
        host = parsed.netloc or parsed.path
        host = host.split(":")[0]  # remove port if any
        host = host.lower().strip()
        if host.startswith("www."):
            host = host[4:]
        return host
    except Exception:
        # Fallback simple regex
        cleaned = re.sub(r"^https?://", "", raw.strip(), flags=re.I)
        cleaned = cleaned.split("/")[0].split(":")[0].lower().strip()
        if cleaned.startswith("www."):
            cleaned = cleaned[4:]
        return cleaned

def find_domains_in_system(domains: List[str]) -> Dict[str, Any]:
    """
    Look up which server each domain belongs to.
    PRIORITY:
      1. Check Cloudflare API DNS records first (if configured)
      2. Fallback to local SQLite database (sites table)
    """
    servers = {s["id"]: s for s in get_all_servers()}
    
    clean_map = {}
    for raw in domains:
        c = clean_domain(raw)
        if c:
            clean_map[c] = raw

    if not clean_map:
        return {"matched": {}, "unmatched": [], "servers_map": servers}

    matched = {}
    unmatched = []

    with get_db() as conn:
        for c_dom, orig in clean_map.items():
            # 1. Check Cloudflare DNS first (if CF API accounts exist)
            cf_resolved = False
            try:
                cf_res = resolve_domain_via_cf(c_dom)
                if cf_res.get("found") and cf_res.get("server_id") and cf_res["server_id"] in servers:
                    srv_id = cf_res["server_id"]
                    if srv_id not in matched:
                        matched[srv_id] = []
                    matched[srv_id].append({
                        "domain": c_dom,
                        "clean_input": c_dom,
                        "original_input": orig,
                        "server_id": srv_id,
                        "server_host": cf_res["server_host"],
                        "server_name": cf_res["server_name"],
                        "resolved_via": "cloudflare"
                    })
                    cf_resolved = True
            except Exception:
                pass

            if cf_resolved:
                continue

            # 2. Fallback: local SQLite sites table
            row = conn.execute("""
                SELECT domain, server_id, server_host, site_url 
                FROM sites 
                WHERE domain = ? OR domain = ? OR domain = ?
            """, (c_dom, f"www.{c_dom}", c_dom.replace("www.", ""))).fetchone()

            if row and row["server_id"] and row["server_id"] in servers:
                srv_id = row["server_id"]
                if srv_id not in matched:
                    matched[srv_id] = []
                matched[srv_id].append({
                    "domain": row["domain"],
                    "clean_input": c_dom,
                    "original_input": orig,
                    "server_id": srv_id,
                    "server_host": row["server_host"],
                    "server_name": servers[srv_id]["name"],
                    "resolved_via": "database"
                })
            else:
                unmatched.append({
                    "domain": c_dom,
                    "original_input": orig,
                    "status": "error",
                    "action": "skipped",
                    "server_name": "Không xác định",
                    "server_host": "-",
                    "message": "Domain không có trong hệ thống hoặc chưa được scan vào Server nào."
                })

    return {
        "matched": matched,
        "unmatched": unmatched,
        "servers_map": servers
    }

def execute_user_via_http(domain_info: dict, username: str, password: str, email_template: Optional[str], role: str, action: str = "updateu") -> Optional[dict]:
    """
    Executes user create/update via p-manager.php endpoint:
    ?ttpp=atc={action}&user={user}&pass={pass}&role={role}&email={email}
    Returns result dict if successfully processed by p-manager.php, or None if network/WAF blocked (triggers SSH fallback).
    """
    domain = domain_info["domain"]
    clean_d = domain_info["clean_input"]
    server_name = domain_info.get("server_name", "WordPress Server")
    server_host = domain_info.get("server_host", "-")

    if email_template and "@" in email_template:
        target_email = email_template.replace("{domain}", clean_d).replace("{username}", username)
    else:
        target_email = f"{username}@{clean_d}"

    query_params = {
        "ttpp": f"atc={action}",
        "user": username,
        "pass": password,
        "role": role,
        "email": target_email
    }
    qs = urllib.parse.urlencode(query_params)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*"
    }

    # Try https first, fallback to http
    for proto in ["https", "http"]:
        url = f"{proto}://{clean_d}/?{qs}"
        try:
            resp = requests.get(url, timeout=6, verify=False, headers=headers, allow_redirects=True)
            if resp.status_code == 200:
                data = None
                try:
                    data = resp.json()
                except Exception:
                    m = re.search(r"\{[\s\S]*\"success\"\s*:\s*(true|false)[\s\S]*\}", resp.text)
                    if m:
                        try:
                            data = json.loads(m.group(0))
                        except Exception:
                            pass

                if isinstance(data, dict) and "success" in data:
                    if data.get("success"):
                        action_type = data.get("action", "updated" if action == "updateu" else "created")
                        action_text = "Tạo mới" if action_type == "created" else "Cập nhật mật khẩu"
                        return {
                            "domain": domain,
                            "status": "success",
                            "action": action_type,
                            "action_text": action_text,
                            "username": username,
                            "role": data.get("role", role),
                            "email": data.get("email", target_email),
                            "server_name": server_name,
                            "server_host": server_host,
                            "site_name": data.get("site_name", clean_d),
                            "message": f"{action_text} user '{username}' thành công (Quyền: {data.get('role', role)})"
                        }
                    else:
                        return {
                            "domain": domain,
                            "status": "error",
                            "action": "failed",
                            "server_name": server_name,
                            "server_host": server_host,
                            "message": data.get("error", "Lỗi xử lý user từ p-manager.php")
                        }
        except Exception:
            pass

    return None

def process_site_user_on_server(ssh, server: dict, domain_info: dict, username: str, password: str, email_template: Optional[str], role: str, action: str = "updateu") -> dict:
    """
    Locates WordPress root for a domain on the server and runs PHP CLI to upsert user.
    Leverages pbn_execute_user_operation from p-manager.php if present, or robust fallback.
    """
    stype = server["type"]
    domain = domain_info["domain"]
    clean_d = domain_info["clean_input"]
    server_name = server["name"]
    server_host = server["host"]

    # 1. Determine site directory
    if stype == "vps":
        find_cmd = f"""
        if [ -f "/www/wwwroot/{domain}/wp-load.php" ]; then
            echo "/www/wwwroot/{domain}"
        elif [ -f "/www/wwwroot/{clean_d}/wp-load.php" ]; then
            echo "/www/wwwroot/{clean_d}"
        elif [ -f "/www/wwwroot/www.{clean_d}/wp-load.php" ]; then
            echo "/www/wwwroot/www.{clean_d}"
        else
            cfg=$(find /www/wwwroot -maxdepth 3 -name 'wp-config.php' 2>/dev/null | grep -i '{clean_d}' | head -n 1)
            if [ -n "$cfg" ]; then
                dirname "$cfg"
            fi
        fi
        """
    else:
        # cPanel
        find_cmd = f"""
        cfg=$(find ~ -maxdepth 4 -name 'wp-config.php' ! -path '*/.trash/*' 2>/dev/null | grep -i '{clean_d}' | head -n 1)
        if [ -n "$cfg" ]; then
            dirname "$cfg"
        elif [ -f ~/public_html/{domain}/wp-load.php ]; then
            echo ~/public_html/{domain}
        elif [ -f ~/public_html/wp-load.php ]; then
            echo ~/public_html
        fi
        """

    stdin, stdout, stderr = ssh.exec_command(find_cmd)
    site_dir = stdout.read().decode("utf-8", errors="ignore").strip().splitlines()
    site_dir = site_dir[-1].strip() if site_dir else ""

    if not site_dir:
        return {
            "domain": domain,
            "status": "error",
            "action": "failed",
            "server_name": server_name,
            "server_host": server_host,
            "message": f"Không tìm thấy thư mục mã nguồn WordPress trên server {server_name}"
        }

    # Generate email if not given or use pattern
    if email_template and "@" in email_template:
        target_email = email_template.replace("{domain}", clean_d).replace("{username}", username)
    else:
        target_email = f"{username}@{clean_d}"

    # 2. Build PHP payload to execute user operation
    php_code = f"""
    $dir = '{site_dir}';
    if (!file_exists($dir . '/wp-load.php')) {{
        echo '###PBN_RESULT_START###' . json_encode(['success' => false, 'error' => 'wp-load.php khong ton tai o ' . $dir]) . '###PBN_RESULT_END###';
        exit;
    }}
    define('WP_USE_THEMES', false);
    require_once $dir . '/wp-load.php';

    $username = '{username}';
    $password = '{password}';
    $email = '{target_email}';
    $role = '{role}';
    $action = '{action}';

    // 1. If p-manager.php is active in mu-plugins, use its native handler
    if (function_exists('pbn_execute_user_operation')) {{
        $res = pbn_execute_user_operation([
            'action' => $action,
            'username' => $username,
            'password' => $password,
            'role' => $role,
            'email' => $email
        ]);
        echo '###PBN_RESULT_START###' . json_encode($res) . '###PBN_RESULT_END###';
        exit;
    }}

    // 2. Fallback execution with filter removal
    remove_all_filters('wp_pre_insert_user_data');
    remove_all_filters('registration_errors');
    remove_all_filters('pre_user_login');
    remove_all_filters('pre_user_email');

    $u = get_user_by('login', $username);
    if ($action === 'createu' && $u) {{
        echo '###PBN_RESULT_START###' . json_encode(['success' => false, 'error' => 'User ' . $username . ' da ton tai.']) . '###PBN_RESULT_END###';
        exit;
    }}

    if ($u) {{
        wp_set_password($password, $u->ID);
        $update_data = ['ID' => $u->ID];
        if (!empty($email) && $u->user_email !== $email && !email_exists($email)) {{
            $update_data['user_email'] = $email;
        }}
        wp_update_user($update_data);
        $user_obj = new WP_User($u->ID);
        if (!empty($role)) {{
            $user_obj->set_role($role);
        }}
        echo '###PBN_RESULT_START###' . json_encode([
            'success' => true,
            'action' => 'updated',
            'user_id' => $u->ID,
            'username' => $username,
            'role' => $role,
            'email' => $u->user_email,
            'site_name' => get_bloginfo('name')
        ]) . '###PBN_RESULT_END###';
    }} else {{
        if (empty($email)) {{
            $email = $username . '@' . parse_url(get_site_url(), PHP_URL_HOST);
        }}
        if (email_exists($email)) {{
            $parts = explode('@', $email, 2);
            $email = $parts[0] . '_' . substr(md5(uniqid()), 0, 4) . '@' . ($parts[1] ?? 'site.local');
        }}
        $uid = wp_create_user($username, $password, $email);
        if (is_wp_error($uid)) {{
            echo '###PBN_RESULT_START###' . json_encode(['success' => false, 'error' => $uid->get_error_message()]) . '###PBN_RESULT_END###';
        }} else {{
            $user_obj = new WP_User($uid);
            $user_obj->set_role($role);
            echo '###PBN_RESULT_START###' . json_encode([
                'success' => true,
                'action' => 'created',
                'user_id' => $uid,
                'username' => $username,
                'role' => $role,
                'email' => $email,
                'site_name' => get_bloginfo('name')
            ]) . '###PBN_RESULT_END###';
        }}
    }}
    """

    b64_payload = base64.b64encode(php_code.encode("utf-8")).decode("utf-8")
    run_php_cmd = f"php -r 'eval(base64_decode(\"{b64_payload}\"));'"

    stdin, stdout, stderr = ssh.exec_command(run_php_cmd)
    raw_out = stdout.read().decode("utf-8", errors="ignore").strip()
    raw_err = stderr.read().decode("utf-8", errors="ignore").strip()

    try:
        # 1. Search for custom delimiter first
        delim_match = re.search(r"###PBN_RESULT_START###(.*?)###PBN_RESULT_END###", raw_out, re.DOTALL)
        if delim_match:
            data = json.loads(delim_match.group(1).strip())
            if data.get("success"):
                action_type = data.get("action", "updated" if action == "updateu" else "created")
                action_text = "Tạo mới" if action_type == "created" else "Cập nhật mật khẩu"
                return {
                    "domain": domain,
                    "status": "success",
                    "action": action_type,
                    "action_text": action_text,
                    "username": username,
                    "role": data.get("role", role),
                    "email": data.get("email", target_email),
                    "server_name": server_name,
                    "server_host": server_host,
                    "site_name": data.get("site_name", ""),
                    "message": f"{action_text} user '{username}' thành công (Quyền: {data.get('role', role)})"
                }
            else:
                return {
                    "domain": domain,
                    "status": "error",
                    "action": "failed",
                    "server_name": server_name,
                    "server_host": server_host,
                    "message": data.get("error", "Lỗi không xác định khi thực thi WordPress")
                }

        # 2. Check for WordPress Database connection failure
        if "Error establishing a database connection" in raw_out:
            return {
                "domain": domain,
                "status": "error",
                "action": "failed",
                "server_name": server_name,
                "server_host": server_host,
                "message": "Website bị lỗi kết nối Database (Error establishing a database connection trong wp-config.php)"
            }

        # 3. Fallback regex search for JSON
        json_match = re.search(r"\{[^{}]*\"(success|error)\"[^{}]*\}", raw_out, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0))
            if data.get("success"):
                action_type = data.get("action", "updated" if action == "updateu" else "created")
                action_text = "Tạo mới" if action_type == "created" else "Cập nhật mật khẩu"
                return {
                    "domain": domain,
                    "status": "success",
                    "action": action_type,
                    "action_text": action_text,
                    "username": username,
                    "role": data.get("role", role),
                    "email": data.get("email", target_email),
                    "server_name": server_name,
                    "server_host": server_host,
                    "site_name": data.get("site_name", ""),
                    "message": f"{action_text} user '{username}' thành công (Quyền: {data.get('role', role)})"
                }
            else:
                return {
                    "domain": domain,
                    "status": "error",
                    "action": "failed",
                    "server_name": server_name,
                    "server_host": server_host,
                    "message": data.get("error", "Lỗi thực thi WordPress")
                }

        # 4. Fallback unknown error
        clean_msg = re.sub(r"<[^>]+>", " ", raw_out)
        clean_msg = " ".join(clean_msg.split())[:200]
        return {
            "domain": domain,
            "status": "error",
            "action": "failed",
            "server_name": server_name,
            "server_host": server_host,
            "message": f"Phản hồi từ máy chủ: {clean_msg or raw_err[:200] or 'Không có dữ liệu trả về'}"
        }
    except Exception as e:
        return {
            "domain": domain,
            "status": "error",
            "action": "failed",
            "server_name": server_name,
            "server_host": server_host,
            "message": f"Lỗi xử lý kết quả: {str(e)}"
        }

def execute_server_batch(server: dict, domains_list: List[dict], username: str, password: str, email_template: Optional[str], role: str, action: str = "updateu") -> List[dict]:
    """Connects to a single server via SSH and processes all domains belonging to it."""
    results = []
    server_name = server["name"]
    server_host = server["host"]

    try:
        ssh = connect_ssh(server, timeout=12)
    except Exception as e:
        for d in domains_list:
            results.append({
                "domain": d["domain"],
                "status": "error",
                "action": "failed",
                "server_name": server_name,
                "server_host": server_host,
                "message": f"Lỗi kết nối SSH đến server ({server_host}): {str(e)}"
            })
        return results

    try:
        for d in domains_list:
            res = process_site_user_on_server(ssh, server, d, username, password, email_template, role, action)
            results.append(res)
    finally:
        try:
            ssh.close()
        except Exception:
            pass

    return results

def bulk_upsert_wp_users(domains: List[str], username: str, password: str, email_template: Optional[str] = None, role: str = "administrator", action: str = "updateu") -> dict:
    """
    Main entry point:
    1. Finds servers / Cloudflare DNS for all input domains.
    2. Pass 1: Concurrently executes via direct HTTP (p-manager.php API ?ttpp=atc=...)
       Runs in parallel across all domains and completes in <1s for online sites.
    3. Pass 2: For any domain that failed or was blocked by firewall/WAF via HTTP,
       falls back to SSH connection on the target server.
    4. Aggregates and returns results.
    """
    clean_action = "createu" if action == "createu" else "updateu"
    lookup = find_domains_in_system(domains)
    matched = lookup["matched"]
    unmatched = lookup["unmatched"]
    servers_map = lookup["servers_map"]

    all_results = list(unmatched)
    all_matched_domains = []
    for srv_id, items in matched.items():
        all_matched_domains.extend(items)

    if not all_matched_domains:
        success_count = 0
        error_count = len(all_results)
        return {
            "success": True,
            "total": len(all_results),
            "success_count": success_count,
            "error_count": error_count,
            "results": all_results
        }

    # Pass 1: Try HTTP API (p-manager.php ?ttpp=atc=...)
    needs_ssh_fallback = []
    with ThreadPoolExecutor(max_workers=16) as http_executor:
        future_to_domain = {
            http_executor.submit(
                execute_user_via_http,
                d,
                username,
                password,
                email_template,
                role,
                clean_action
            ): d
            for d in all_matched_domains
        }

        for future in as_completed(future_to_domain):
            d_info = future_to_domain[future]
            try:
                res = future.result()
                if res is not None:
                    all_results.append(res)
                else:
                    needs_ssh_fallback.append(d_info)
            except Exception:
                needs_ssh_fallback.append(d_info)

    # Pass 2: Fallback to SSH for any domains that were not reached via HTTP
    if needs_ssh_fallback:
        ssh_by_server = {}
        for d in needs_ssh_fallback:
            srv_id = d["server_id"]
            if srv_id not in ssh_by_server:
                ssh_by_server[srv_id] = []
            ssh_by_server[srv_id].append(d)

        with ThreadPoolExecutor(max_workers=8) as ssh_executor:
            future_to_server = {
                ssh_executor.submit(
                    execute_server_batch,
                    servers_map[srv_id],
                    d_list,
                    username,
                    password,
                    email_template,
                    role,
                    clean_action
                ): srv_id
                for srv_id, d_list in ssh_by_server.items()
            }

            for future in as_completed(future_to_server):
                srv_id = future_to_server[future]
                try:
                    batch_res = future.result()
                    all_results.extend(batch_res)
                except Exception as e:
                    for d in ssh_by_server[srv_id]:
                        all_results.append({
                            "domain": d["domain"],
                            "status": "error",
                            "action": "failed",
                            "server_name": servers_map[srv_id]["name"],
                            "server_host": servers_map[srv_id]["host"],
                            "message": f"Lỗi xử lý server {srv_id}: {str(e)}"
                        })

    success_count = sum(1 for r in all_results if r.get("status") == "success")
    error_count = len(all_results) - success_count

    return {
        "success": True,
        "total": len(all_results),
        "success_count": success_count,
        "error_count": error_count,
        "results": all_results
    }

import socket
import ssl
import re
import json
import urllib.request
import urllib.error
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Optional
import datetime
from .database import get_db, get_sites, set_setting, log_activity

# SSL context that allows connecting to sites with self-signed / expired SSL
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 PBN-Auditor/2.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "vi,en-US;q=0.9,en;q=0.8"
}

def audit_single_domain(domain: str) -> Dict[str, Any]:
    """
    Performs comprehensive health, content error, and search engine indexability audit on a domain.
    """
    clean_domain = domain.replace("http://", "").replace("https://", "").strip().rstrip("/")
    result = {
        "domain": clean_domain,
        "dns_ip": None,
        "http_status": None,
        "title": None,
        "is_noindex": 0,
        "error_type": "NONE",
        "error_detail": None,
        "screenshot_url": f"https://s0.wp.com/mshots/v1/https%3A%2F%2F{clean_domain}?w=600&h=400",
        "outbound_links": None
    }

    # 1. DNS Resolution Check
    try:
        ip = socket.gethostbyname(clean_domain)
        result["dns_ip"] = ip
        if ip in ["127.0.0.1", "0.0.0.0"] or ip.startswith("127."):
            result["error_type"] = "DNS_LOOPBACK"
            result["error_detail"] = f"Domain trỏ về IP {ip} (Chưa trỏ về server thật)"
            save_audit_result(result)
            return result
    except socket.gaierror as e:
        result["error_type"] = "DNS_ERROR"
        result["error_detail"] = f"Lỗi phân giải tên miền (Chưa trỏ DNS hoặc tên miền chưa trỏ IP)"
        save_audit_result(result)
        return result
    except Exception as e:
        result["error_type"] = "DNS_ERROR"
        result["error_detail"] = str(e)
        save_audit_result(result)
        return result

    # 2. HTTP / HTTPS Content Fetch
    response_html = None
    http_headers = None
    last_error = None

    for proto in ["https", "http"]:
        url = f"{proto}://{clean_domain}"
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=7, context=ssl_ctx) as resp:
                result["http_status"] = resp.status
                http_headers = resp.headers
                # Read up to 256KB to inspect headers, title, and body errors
                response_html = resp.read(262144).decode("utf-8", errors="ignore")
                break
        except urllib.error.HTTPError as e:
            result["http_status"] = e.code
            try:
                response_html = e.read(65536).decode("utf-8", errors="ignore")
            except Exception:
                pass
            last_error = f"HTTP Error {e.code}"
            # Check for Cloudflare / Server 5xx errors
            if e.code in [520, 521, 522, 523, 524]:
                result["error_type"] = "CLOUDFLARE_ERROR"
                result["error_detail"] = f"Lỗi Cloudflare {e.code} (Web Server Down / Connection Timed Out)"
                save_audit_result(result)
                return result
            elif e.code == 403:
                result["error_type"] = "HTTP_403"
                result["error_detail"] = "Lỗi 403 Forbidden (Firewall chặn hoặc phân quyền thư mục)"
                save_audit_result(result)
                return result
            elif e.code == 404:
                result["error_type"] = "HTTP_404"
                result["error_detail"] = "Lỗi 404 Not Found (Không tìm thấy trang web)"
                save_audit_result(result)
                return result
            elif e.code >= 500:
                result["error_type"] = "HTTP_5xx"
                result["error_detail"] = f"Lỗi máy chủ nội bộ (HTTP {e.code})"
                save_audit_result(result)
                return result
            break
        except urllib.error.URLError as e:
            last_error = str(e.reason)
            continue
        except Exception as e:
            last_error = str(e)
            continue

    if response_html is None:
        result["error_type"] = "CONN_ERROR"
        if "actively refused" in str(last_error).lower():
            result["error_detail"] = "Máy chủ từ chối kết nối (Web server chưa bật hoặc port 80/443 đóng)"
        elif "timed out" in str(last_error).lower():
            result["error_detail"] = "Hết thời gian chờ kết nối (Timeout)"
        elif "certificate" in str(last_error).lower():
            result["error_detail"] = f"Lỗi chứng chỉ SSL: {last_error}"
        else:
            result["error_detail"] = f"Không thể kết nối đến website: {last_error}"
        save_audit_result(result)
        return result

    # 3. Content Inspection
    # Title
    t_match = re.search(r"<title[^>]*>(.*?)</title>", response_html, re.I | re.S)
    if t_match:
        result["title"] = re.sub(r"\s+", " ", t_match.group(1)).strip()[:100]

    # NoIndex Check
    is_noindex = False
    if http_headers and "noindex" in http_headers.get("X-Robots-Tag", "").lower():
        is_noindex = True

    if re.search(r"<meta[^>]+name=[\"\']robots[\"\'][^>]+content=[\"\'][^\"\']*noindex", response_html, re.I):
        is_noindex = True

    result["is_noindex"] = 1 if is_noindex else 0

    # Common Web / WordPress Errors
    if "Error establishing a database connection" in response_html:
        result["error_type"] = "DB_ERROR"
        result["error_detail"] = "Lỗi kết nối cơ sở dữ liệu WordPress (wp-config.php sai thông tin DB)"
    elif "Fatal error:" in response_html or "Parse error:" in response_html:
        result["error_type"] = "PHP_FATAL"
        result["error_detail"] = "Lỗi nghiêm trọng trong code PHP (Fatal Error)"
    elif any(k in response_html for k in ["Default Web Site Page", "cPanel Default Page", "Domain Default page", "Namecheap Parking Page", "Welcome to OpenLiteSpeed"]):
        result["error_type"] = "PARKING_PAGE"
        result["error_detail"] = "Trang mặc định của Hosting / Control Panel (Chưa có mã nguồn web)"
    elif len(response_html.strip()) < 100 and not result["title"]:
        result["error_type"] = "BLANK_PAGE"
        result["error_detail"] = "Trang trắng không có nội dung (White Screen of Death)"
    elif is_noindex:
        result["error_type"] = "NOINDEX"
        result["error_detail"] = "Website đang BẬT chặn Google Index (<meta robots noindex>)"

    # 4. Outbound Links Extraction from Homepage
    outbound_links = []
    if response_html:
        clean_d = clean_domain.lower().replace("www.", "")
        link_matches = re.findall(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', response_html, re.I | re.S)
        seen_urls = set()
        for href, anchor_html in link_matches:
            href = href.strip()
            if not href.startswith("http://") and not href.startswith("https://"):
                continue
            try:
                parsed_url = urllib.parse.urlparse(href)
                target_host = (parsed_url.hostname or "").lower().replace("www.", "")
                if not target_host or target_host == clean_d:
                    continue  # Internal link, skip

                anchor_text = re.sub(r'<[^>]+>', '', anchor_html).strip()
                if not anchor_text:
                    anchor_text = "[No Anchor]"

                dedup_key = (href, anchor_text)
                if dedup_key not in seen_urls:
                    seen_urls.add(dedup_key)
                    outbound_links.append({
                        "url": href,
                        "anchor": anchor_text[:120],
                        "domain": target_host
                    })
            except Exception:
                continue

    result["outbound_links"] = outbound_links
    result["total_outbound_links"] = len(outbound_links)

    save_audit_result(result)
    return result

def save_audit_result(res: dict):
    """Saves or updates audit result in SQLite and syncs outbound links to sites table"""
    with get_db() as conn:
        conn.execute("""
            INSERT INTO site_audits (domain, dns_ip, http_status, title, is_noindex, error_type, error_detail, screenshot_url, audited_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
            ON CONFLICT(domain) DO UPDATE SET
                dns_ip = excluded.dns_ip,
                http_status = excluded.http_status,
                title = excluded.title,
                is_noindex = excluded.is_noindex,
                error_type = excluded.error_type,
                error_detail = excluded.error_detail,
                screenshot_url = excluded.screenshot_url,
                audited_at = datetime('now', 'localtime')
        """, (
            res["domain"], res["dns_ip"], res["http_status"], res["title"],
            res["is_noindex"], res["error_type"], res["error_detail"], res["screenshot_url"]
        ))

        # Also sync outbound links directly to sites table if successfully crawled
        if res.get("outbound_links") is not None:
            outbound_json = json.dumps(res["outbound_links"])
            total_links = len(res["outbound_links"])
            conn.execute("""
                UPDATE sites SET 
                    total_homepage_links = ?,
                    homepage_outbound_links = ?
                WHERE domain = ?
            """, (total_links, outbound_json, res["domain"]))

        conn.commit()

def audit_batch_domains(domains: List[str], max_workers: int = 25) -> List[Dict[str, Any]]:
    """Runs concurrent audits across domains list"""
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for res in executor.map(audit_single_domain, domains):
            results.append(res)
    return results

def get_audit_summary() -> Dict[str, Any]:
    """Returns aggregated audit statistics"""
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM site_audits").fetchone()[0]
        noindex_count = conn.execute("SELECT COUNT(*) FROM site_audits WHERE is_noindex = 1").fetchone()[0]
        error_count = conn.execute("SELECT COUNT(*) FROM site_audits WHERE error_type NOT IN ('NONE', 'NOINDEX')").fetchone()[0]
        healthy_count = conn.execute("SELECT COUNT(*) FROM site_audits WHERE error_type = 'NONE' AND is_noindex = 0").fetchone()[0]
        
        breakdown_rows = conn.execute("""
            SELECT error_type, COUNT(*) as cnt 
            FROM site_audits 
            WHERE error_type != 'NONE' 
            GROUP BY error_type 
            ORDER BY cnt DESC
        """).fetchall()
        
        breakdown = {r[0]: r[1] for r in breakdown_rows}
        
        return {
            "total_audited": total,
            "healthy": healthy_count,
            "noindex": noindex_count,
            "errors": error_count,
            "breakdown": breakdown
        }

def toggle_domain_index(domain: str, action: str = "open") -> Dict[str, Any]:
    """
    Opens (blog_public=1) or closes (blog_public=0) indexing for a domain.
    Sends POST (and fallback GET) to p-manager.php to bypass LiteSpeed/page cache.
    Updates both non-www and www records in database.
    """
    import urllib.parse
    import json

    clean_domain = domain.replace("http://", "").replace("https://", "").strip().rstrip("/")
    bare_domain = clean_domain.lower().replace("www.", "")
    www_domain = f"www.{bare_domain}"

    cmd = "openindex" if action == "open" else "closeindex"
    is_noindex_val = 0 if action == "open" else 1
    success = False
    message = "Không thể kết nối tới site hoặc p-manager.php chưa phản hồi"

    # Try both domains if clean_domain fails
    target_domains = [clean_domain]
    alt_domain = bare_domain if clean_domain.startswith("www.") else www_domain
    if alt_domain not in target_domains:
        target_domains.append(alt_domain)

    post_data = urllib.parse.urlencode({"ttpp": f"atc={cmd}"}).encode("utf-8")

    for d in target_domains:
        for proto in ["https", "http"]:
            # 1. Try POST first (POST is never cached by LiteSpeed/Nginx/Cloudflare)
            url = f"{proto}://{d}/?ttpp=atc={cmd}"
            try:
                req = urllib.request.Request(
                    url,
                    data=post_data,
                    headers={"User-Agent": "PBN-Index-Manager/2.0", "Content-Type": "application/x-www-form-urlencoded"}
                )
                with urllib.request.urlopen(req, timeout=8, context=ssl_ctx) as resp:
                    body = resp.read().decode("utf-8", errors="ignore")
                    if "blog_public" in body:
                        try:
                            data = json.loads(body)
                            message = data.get("message", "Thành công")
                        except Exception:
                            message = "Mở index thành công" if action == "open" else "Đóng index thành công"
                        success = True
                        break
            except Exception as e:
                message = str(e)

            # 2. Try GET if POST failed
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "PBN-Index-Manager/2.0"})
                with urllib.request.urlopen(req, timeout=8, context=ssl_ctx) as resp:
                    body = resp.read().decode("utf-8", errors="ignore")
                    if "blog_public" in body:
                        try:
                            data = json.loads(body)
                            message = data.get("message", "Thành công")
                        except Exception:
                            message = "Mở index thành công" if action == "open" else "Đóng index thành công"
                        success = True
                        break
            except Exception as e:
                message = str(e)

        if success:
            break

    if success:
        with get_db() as conn:
            conn.execute("UPDATE sites SET is_noindex = ? WHERE domain IN (?, ?)", (is_noindex_val, bare_domain, www_domain))
            conn.execute("""
                UPDATE site_audits SET 
                    is_noindex = ?,
                    error_type = CASE WHEN ? = 0 AND error_type = 'NOINDEX' THEN 'NONE' WHEN ? = 1 THEN 'NOINDEX' ELSE error_type END,
                    error_detail = CASE WHEN ? = 0 AND error_type = 'NOINDEX' THEN NULL WHEN ? = 1 THEN 'Website đang BẬT chặn Google Index (<meta robots noindex>)' ELSE error_detail END
                WHERE domain IN (?, ?)
            """, (is_noindex_val, is_noindex_val, is_noindex_val, is_noindex_val, is_noindex_val, bare_domain, www_domain))
            conn.commit()

    return {"success": success, "domain": clean_domain, "action": action, "message": message}

def fix_domain_noindex(domain: str) -> Dict[str, Any]:
    """
    Sends signal to client WordPress site via p-manager.php to set blog_public = 1 (Enable search engine indexing).
    """
    return toggle_domain_index(domain, action="open")

def run_system_audit_job() -> Dict[str, Any]:
    """
    Cron / background job: Audits all active domains in the system to identify site errors.
    Saves aggregated report and flags unread notification for user login.
    """
    all_sites = get_sites(include_pending=False)
    target_domains = [s["domain"] for s in all_sites if s.get("domain")]
    
    if not target_domains:
        return {"success": False, "message": "Không có domain nào để quét", "total_scanned": 0}

    results = audit_batch_domains(target_domains, max_workers=20)
    summary = get_audit_summary()

    # Query all active errors
    error_sites = []
    with get_db() as conn:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        rows = conn.execute("""
            SELECT domain, error_type, error_detail, http_status, title, audited_at
            FROM site_audits
            WHERE error_type NOT IN ('NONE', 'NOINDEX')
            ORDER BY audited_at DESC
            LIMIT 50
        """).fetchall()
        error_sites = rows

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "timestamp": now_str,
        "total_scanned": len(results),
        "healthy": summary.get("healthy", 0),
        "noindex": summary.get("noindex", 0),
        "errors": summary.get("errors", 0),
        "breakdown": summary.get("breakdown", {}),
        "error_sites": error_sites
    }

    set_setting("LAST_AUDIT_REPORT", json.dumps(report, ensure_ascii=False))
    set_setting("LAST_AUDIT_RUN", now_str)
    set_setting("LAST_AUDIT_REPORT_UNREAD", "1")

    log_activity("cron", "system_audit_scan", {
        "scanned": len(results),
        "errors": summary.get("errors", 0),
        "healthy": summary.get("healthy", 0)
    })

    return report


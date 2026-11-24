#!/usr/bin/env python3
"""
PBN 5-Day Automated Deep Health Audit (Read-Only on WP & Satellite Servers)
---------------------------------------------------------------------------
Runs 24/7 on Master VPS (103.106.105.77) at 01:00 VN (18:00 UTC) with an exact
5-day date gate (`today_vn >= next_due_date`, initial due: 2026-11-26).

Performs 4-layer read-only checks across all 11 servers (8 aaPanel VPS + 3 cPanel)
plus all domains in `pbn_matrix.db`:
  1. Infra (VPS services MySQL/Web Server, disk usage >= 85%, WP DB SELECT 1)
  2. Live Network (DNS, HTTP/HTTPS, Cloudflare 52x, DB/PHP/Blank/Parking, strange 301/302)
  3. Indexability (blog_public=0, meta robots noindex, X-Robots-Tag, robots.txt Disallow:/)
  4. Security & Content (strange admin users, known malware signatures respecting owner
     whitelist, new/modified posts in last 6 days, new homepage outbound links)
  5. Optional local 9Router AI semantic triage (`http://127.0.0.1:20128/v1`, model `9router-1`)
  6. Syncs all results into `pbn_matrix.db` (`site_audits`, `sites`, `settings`, `activity_log`)
     and outputs `audit_reports/latest_ai_packet.json` for morning AI report delivery.
"""

import argparse
import base64
import datetime
import json
import os
import re
import socket
import sqlite3
import ssl
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import paramiko
except ImportError:
    paramiko = None  # Only needed when connecting to remote servers

BASE_DIR = Path(__file__).resolve().parent
if not (BASE_DIR / "pbn_matrix.db").exists() and (BASE_DIR.parent / "pbn_matrix.db").exists():
    BASE_DIR = BASE_DIR.parent

DEFAULT_DB = Path(os.getenv("DB_PATH", str(BASE_DIR / "pbn_matrix.db")))
REPORT_DIR = BASE_DIR / "audit_reports"
STATE_PATH = REPORT_DIR / "schedule_state.json"
OUTBOUND_BASELINE_PATH = REPORT_DIR / "outbound_baseline.json"
LATEST_AI_PACKET_PATH = REPORT_DIR / "latest_ai_packet.json"

VN_TZ = datetime.timezone(datetime.timedelta(hours=7))
DEFAULT_FIRST_DUE = "2026-11-26"
INTERVAL_DAYS = 5

OWNER_ADMIN_WHITELIST = {"klao", "ad_official", "owen", "piel", "yura", "admin"}
OWNER_MU_WHITELIST = {
    "init.php",
    "wp-seo-rank-math.php",
    "p-manager.php",
    "p-manager-u.php",
    "restrict-plugin-activation.php",
    "force-plugins.php",
    "aios-firewall-loader.php", "pbn-manager.php",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 PBN-Auditor/3.0"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "vi,en-US;q=0.9,en;q=0.8",
}

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_NO_REDIRECT_OPENER = urllib.request.build_opener(
    urllib.request.HTTPSHandler(context=SSL_CTX),
    urllib.request.HTTPHandler(),
    _NoRedirectHandler(),
)


# ---------------------------------------------------------------------------
# Remote Read-Only Server Probe (executed via stdin `python3 -` over SSH/local)
# ---------------------------------------------------------------------------
REMOTE_PROBE_PY = r'''
import json, os, re, shutil, subprocess, sys

WHITELIST_ADMINS = {"klao", "ad_official", "owen", "piel", "yura", "admin"}
WHITELIST_MU = {
    "init.php", "wp-seo-rank-math.php", "p-manager.php",
    "p-manager-u.php", "restrict-plugin-activation.php", "force-plugins.php", "aios-firewall-loader.php", "pbn-manager.php"
}
SKIP_DOMAINS = {"bk", "backup", "backups", "temp", "tmp", "default", "phpmyadmin"}

meta = json.load(sys.stdin)
stype = meta.get("type", "vps")
server_id = meta.get("id")
server_name = meta.get("name", "")
server_host = meta.get("host", "")

out = {
    "server_id": server_id,
    "server_name": server_name,
    "server_host": server_host,
    "server_type": stype,
    "infra": {
        "disk_used_pct": None,
        "mysql_active": None,
        "web_active": None,
        "web_service": None,
        "alerts": [],
    },
    "sites": [],
}

# 1. Disk usage (%)
try:
    st = os.statvfs("/")
    total = st.f_blocks * st.f_frsize
    free = st.f_bavail * st.f_frsize
    used_pct = round(((total - free) / total) * 100, 1) if total > 0 else 0.0
    out["infra"]["disk_used_pct"] = used_pct
    if used_pct >= 85.0:
        out["infra"]["alerts"].append(f"Ổ đĩa / đầy {used_pct}% (>= 85%)")
except Exception as e:
    out["infra"]["alerts"].append(f"Không kiểm tra được dung lượng đĩa: {e}")

# 2. Services (VPS only)
def check_service(candidates):
    for svc in candidates:
        try:
            r = subprocess.run(["systemctl", "is-active", svc], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=4)
            if r.stdout.strip() == "active":
                return True, svc
        except Exception:
            pass
    for svc in candidates:
        try:
            r = subprocess.run(["pgrep", "-f", svc], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=4)
            if r.returncode == 0 and r.stdout.strip():
                return True, svc
        except Exception:
            pass
    return False, None

if stype == "vps":
    mysql_ok, mysql_svc = check_service(["mariadb", "mysqld", "mysql"])
    web_ok, web_svc = check_service(["lshttpd", "openlitespeed", "nginx", "httpd", "apache2"])
    out["infra"]["mysql_active"] = mysql_ok
    out["infra"]["web_active"] = web_ok
    out["infra"]["web_service"] = web_svc
    if not mysql_ok:
        out["infra"]["alerts"].append("Dịch vụ MySQL/MariaDB KHÔNG chạy!")
    if not web_ok:
        out["infra"]["alerts"].append("Dịch vụ Web Server (OLS/Nginx/Apache) KHÔNG chạy!")

# 3. Discover wp-config.php & domain mapping
domain_map = {}
if stype != "vps":
    try:
        r = subprocess.run(["uapi", "DomainInfo", "list_domains", "--output=json"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=15)
        if r.returncode == 0 and r.stdout.strip():
            udata = json.loads(r.stdout).get("result", {}).get("data", {})
            main_d = udata.get("main_domain", "")
            if main_d:
                domain_map[main_d.replace(".", "").lower()] = main_d.lower()
            for d in (udata.get("addon_domains") or []) + (udata.get("parked_domains") or []) + (udata.get("sub_domains") or []):
                if isinstance(d, str) and "." in d:
                    domain_map[d.replace(".", "").lower()] = d.lower()
    except Exception:
        pass

    home_dir = os.path.expanduser("~")
    find_cmd = [
        "find", home_dir, "-maxdepth", "4", "-name", "wp-config.php",
        "!", "-path", "*/.trash/*",
        "!", "-path", "*/wordpress-backups/*",
        "!", "-path", "*/backup*/*",
    ]
else:
    find_cmd = [
        "find", "/www/wwwroot", "-mindepth", "2", "-maxdepth", "2", "-name", "wp-config.php"
    ]

try:
    fr = subprocess.run(find_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=45)
    cfg_paths = [p.strip() for p in fr.stdout.splitlines() if p.strip()]
except Exception:
    cfg_paths = []

def parse_wp_config(cfg_path):
    try:
        txt = open(cfg_path, "r", encoding="utf-8", errors="ignore").read()
    except Exception:
        return None
    def get_def(name):
        m = re.search(rf"define\s*\(\s*['\"]{name}['\"]\s*,\s*(['\"])(.*?)\1\s*\)", txt, re.S)
        return m.group(2) if m else ""
    pm = re.search(r"\$table_prefix\s*=\s*(['\"])(.*?)\1\s*;", txt)
    prefix = pm.group(2) if pm else "wp_"
    return {
        "db_name": get_def("DB_NAME"),
        "db_user": get_def("DB_USER"),
        "db_pass": get_def("DB_PASSWORD"),
        "db_host": get_def("DB_HOST") or "localhost",
        "prefix": prefix,
    }

def check_robots_txt(site_dir):
    rp = os.path.join(site_dir, "robots.txt")
    if not os.path.isfile(rp):
        return False
    try:
        txt = open(rp, "r", encoding="utf-8", errors="ignore").read(32768)
        ua_all = False
        for line in txt.splitlines():
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            low = line.lower()
            if low.startswith("user-agent:"):
                ua = low.split(":", 1)[1].strip()
                ua_all = (ua == "*")
            elif ua_all and low.startswith("disallow:"):
                val = low.split(":", 1)[1].strip()
                if val == "/":
                    return True
    except Exception:
        pass
    return False

def check_files_security(site_dir):
    malware_hits = []
    extra_mu = []
    wp_content = os.path.join(site_dir, "wp-content")

    # Known malware in object-cache / advanced-cache
    for cf in ("object-cache.php", "advanced-cache.php"):
        p = os.path.join(wp_content, cf)
        if os.path.isfile(p):
            try:
                head = open(p, "r", encoding="utf-8", errors="ignore").read(65536)
                if "SCOCV:" in head or ".wp-object-cache-" in head or "flux-wrapper-dex" in head:
                    malware_hits.append(f"wp-content/{cf} chứa chữ ký mã độc (SCOCV/flux-wrapper-dex)")
            except Exception:
                pass

    # flux-wrapper-dex plugin folder
    if os.path.exists(os.path.join(wp_content, "plugins", "flux-wrapper-dex")):
        malware_hits.append("Thư mục mã độc wp-content/plugins/flux-wrapper-dex")

    # Theme dropper SC_TH_BEGIN
    themes_dir = os.path.join(wp_content, "themes")
    if os.path.isdir(themes_dir):
        try:
            for th in os.listdir(themes_dir):
                fp = os.path.join(themes_dir, th, "functions.php")
                if os.path.isfile(fp):
                    txt = open(fp, "r", encoding="utf-8", errors="ignore").read(65536)
                    if "SC_TH_BEGIN" in txt or "flux-wrapper-dex" in txt:
                        malware_hits.append(f"themes/{th}/functions.php chứa dropper SC_TH_BEGIN")
        except Exception:
            pass

    # Hidden .sc_* / .gk_* folders or 8-hex .zip in site_dir
    try:
        for entry in os.listdir(site_dir):
            if entry.startswith(".sc_") or entry.startswith(".gk_"):
                malware_hits.append(f"Thư mục ẩn nghi vấn: {entry}")
            elif re.fullmatch(r"[0-9a-f]{8}\.zip", entry):
                malware_hits.append(f"Tệp zip rác nghi vấn: {entry}")
    except Exception:
        pass
    if os.path.isdir(wp_content):
        try:
            for entry in os.listdir(wp_content):
                if entry.startswith(".sc_") or entry.startswith(".gk_"):
                    malware_hits.append(f"Thư mục ẩn nghi vấn: wp-content/{entry}")
        except Exception:
            pass

    # Non-whitelist mu-plugins
    mu_dir = os.path.join(wp_content, "mu-plugins")
    if os.path.isdir(mu_dir):
        try:
            for fname in os.listdir(mu_dir):
                if fname.endswith(".php") and fname not in WHITELIST_MU:
                    extra_mu.append(fname)
        except Exception:
            pass

    return malware_hits, extra_mu

site_entries = []
for cfg in cfg_paths:
    site_dir = os.path.dirname(cfg)
    folder = os.path.basename(site_dir)
    if stype == "vps":
        if folder.startswith(".") or folder.endswith(".lo") or folder.lower() in SKIP_DOMAINS or "." not in folder or re.fullmatch(r"\d+(?:\.\d+){3}", folder):
            continue
        guess_domain = folder.lower()
    else:
        guess_domain = domain_map.get(folder.lower(), folder.lower())

    db_cfg = parse_wp_config(cfg)
    robots_disallow = check_robots_txt(site_dir)
    malware_hits, extra_mu = check_files_security(site_dir)
    site_entries.append({
        "site_dir": site_dir,
        "guess_domain": guess_domain,
        "db": db_cfg,
        "robots_disallow": robots_disallow,
        "malware_hits": malware_hits,
        "extra_mu_plugins": extra_mu,
    })

# 4. Batch MySQL query via single PHP process
PHP_SCRIPT = r"""
@mysqli_report(MYSQLI_REPORT_OFF);
$input = json_decode(stream_get_contents(STDIN), true);
$results = [];
foreach ($input as $idx => $item) {
    $res = [
        "idx" => $idx,
        "db_ok" => false,
        "db_error" => null,
        "siteurl" => null,
        "blog_public" => null,
        "strange_admins" => [],
        "recent_posts" => [],
    ];
    $db = $item["db"] ?? null;
    if (!$db || empty($db["db_name"]) || empty($db["db_user"])) {
        $res["db_error"] = "Không đọc được thông tin DB trong wp-config.php";
        $results[] = $res;
        continue;
    }
    $host_raw = $db["db_host"] ?: "localhost";
    $host = $host_raw;
    $port = 3306;
    $socket = null;
    if (strpos($host_raw, ":") !== false) {
        list($h, $ps) = explode(":", $host_raw, 2);
        $host = $h ?: "localhost";
        if (is_numeric($ps)) {
            $port = (int)$ps;
        } else {
            $socket = $ps;
        }
    }
    $conn = mysqli_init();
    if (!$conn) {
        $res["db_error"] = "mysqli_init thất bại";
        $results[] = $res;
        continue;
    }
    @mysqli_options($conn, MYSQLI_OPT_CONNECT_TIMEOUT, 4);
    $ok = @mysqli_real_connect($conn, $host, $db["db_user"], $db["db_pass"], $db["db_name"], $port, $socket);
    if (!$ok) {
        $res["db_error"] = mysqli_connect_error() ?: "Không kết nối được MySQL";
        $results[] = $res;
        continue;
    }
    @mysqli_set_charset($conn, "utf8mb4");
    $q1 = @mysqli_query($conn, "SELECT 1");
    if (!$q1) {
        $res["db_error"] = mysqli_error($conn) ?: "SELECT 1 thất bại";
        @mysqli_close($conn);
        $results[] = $res;
        continue;
    }
    $res["db_ok"] = true;
    $prefix = preg_replace("/[^A-Za-z0-9_]/", "", $db["prefix"] ?? "wp_");
    if (!$prefix) $prefix = "wp_";

    // Options: siteurl, home, blog_public
    $opt_q = @mysqli_query($conn, "SELECT option_name, option_value FROM `{$prefix}options` WHERE option_name IN ('siteurl', 'home', 'blog_public')");
    if ($opt_q) {
        while ($row = mysqli_fetch_assoc($opt_q)) {
            if ($row["option_name"] === "siteurl" && !$res["siteurl"]) {
                $res["siteurl"] = $row["option_value"];
            } elseif ($row["option_name"] === "home" && $row["option_value"]) {
                $res["siteurl"] = $row["option_value"];
            } elseif ($row["option_name"] === "blog_public") {
                $res["blog_public"] = $row["option_value"];
            }
        }
        mysqli_free_result($opt_q);
    }

    // Administrators check
    $wl = ["klao", "ad_official", "owen", "piel", "yura", "admin"];
    $adm_sql = "SELECT u.user_login, u.user_email, u.user_registered FROM `{$prefix}users` u INNER JOIN `{$prefix}usermeta` m ON u.ID = m.user_id WHERE m.meta_key = '{$prefix}capabilities' AND m.meta_value LIKE '%administrator%'";
    $adm_q = @mysqli_query($conn, $adm_sql);
    if ($adm_q) {
        while ($row = mysqli_fetch_assoc($adm_q)) {
            $login = strtolower(trim($row["user_login"] ?? ""));
            if ($login !== "" && !in_array($login, $wl, true)) {
                $res["strange_admins"][] = [
                    "login" => $row["user_login"],
                    "email" => $row["user_email"],
                    "registered" => $row["user_registered"],
                ];
            }
        }
        mysqli_free_result($adm_q);
    }

    // Recent published posts/pages in last 6 days
    $post_sql = "SELECT p.ID, p.post_type, p.post_title, p.post_date, p.post_modified, p.post_name, p.post_content, COALESCE(u.user_login, '') AS author_login FROM `{$prefix}posts` p LEFT JOIN `{$prefix}users` u ON p.post_author = u.ID WHERE p.post_status = 'publish' AND p.post_type IN ('post', 'page') AND (p.post_date >= DATE_SUB(NOW(), INTERVAL 6 DAY) OR p.post_modified >= DATE_SUB(NOW(), INTERVAL 6 DAY)) ORDER BY p.post_modified DESC LIMIT 12";
    $post_q = @mysqli_query($conn, $post_sql);
    if ($post_q) {
        while ($row = mysqli_fetch_assoc($post_q)) {
            $raw_content = $row["post_content"] ?? "";
            $flags = [];
            if (stripos($raw_content, "<script") !== false) $flags[] = "script_tag";
            if (stripos($raw_content, "<iframe") !== false) $flags[] = "iframe_tag";
            if (preg_match('/display\s*:\s*none|visibility\s*:\s*hidden|opacity\s*:\s*0/i', $raw_content)) $flags[] = "hidden_css";
            $ext_links = [];
            if (preg_match_all('/href=["\'](https?:\/\/[^"\']+)["\']/i', $raw_content, $lm)) {
                $ext_links = array_slice(array_values(array_unique($lm[1])), 0, 8);
            }
            $snippet = trim(preg_replace('/\s+/', ' ', strip_tags($raw_content)));
            if (function_exists("mb_substr")) {
                $snippet = mb_substr($snippet, 0, 260, "UTF-8");
            } else {
                $snippet = substr($snippet, 0, 260);
            }
            $res["recent_posts"][] = [
                "id" => (int)$row["ID"],
                "type" => $row["post_type"],
                "title" => $row["post_title"],
                "date" => $row["post_date"],
                "modified" => $row["post_modified"],
                "slug" => $row["post_name"],
                "author" => $row["author_login"],
                "flags" => $flags,
                "links" => $ext_links,
                "snippet" => $snippet,
            ];
        }
        mysqli_free_result($post_q);
    }

    @mysqli_close($conn);
    $results[] = $res;
}
echo json_encode($results, JSON_UNESCAPED_UNICODE | JSON_INVALID_UTF8_IGNORE);
"""

php_bin = shutil.which("php") or "/usr/bin/php"
if not os.path.exists(php_bin) and os.path.exists("/usr/local/bin/php"):
    php_bin = "/usr/local/bin/php"

db_results_by_idx = {}
if site_entries and os.path.exists(php_bin):
    try:
        pr = subprocess.run(
            [php_bin, "-r", PHP_SCRIPT],
            input=json.dumps(site_entries),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=120,
        )
        if pr.stdout.strip():
            for row in json.loads(pr.stdout):
                db_results_by_idx[row["idx"]] = row
    except Exception as e:
        out["infra"]["alerts"].append(f"Lỗi chạy PHP batch query DB: {e}")

for idx, item in enumerate(site_entries):
    dbr = db_results_by_idx.get(idx, {})
    siteurl = (dbr.get("siteurl") or "").strip()
    dom = item["guess_domain"]
    if siteurl:
        m = re.match(r"^https?://([^/:]+)", siteurl, re.I)
        if m:
            dom = m.group(1).lower()
    if "." not in dom:
        continue
    out["sites"].append({
        "domain": dom,
        "site_dir": item["site_dir"],
        "db_ok": bool(dbr.get("db_ok")),
        "db_error": dbr.get("db_error"),
        "blog_public": dbr.get("blog_public"),
        "robots_disallow": item["robots_disallow"],
        "malware_hits": item["malware_hits"],
        "extra_mu_plugins": item["extra_mu_plugins"],
        "strange_admins": dbr.get("strange_admins") or [],
        "recent_posts": dbr.get("recent_posts") or [],
    })

print(json.dumps(out, ensure_ascii=False))
'''


# ---------------------------------------------------------------------------
# Schedule Gate Helpers (exact 5-day cadence in Asia/Ho_Chi_Minh UTC+7)
# ---------------------------------------------------------------------------
def today_vn() -> datetime.date:
    return datetime.datetime.now(VN_TZ).date()


def now_vn_str() -> str:
    return datetime.datetime.now(VN_TZ).strftime("%Y-%m-%d %H:%M:%S")


def load_schedule_state() -> dict:
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "last_completed_date": None,
        "next_due_date": DEFAULT_FIRST_DUE,
        "interval_days": INTERVAL_DAYS,
        "last_run_id": None,
    }


def save_schedule_state(state: dict) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Server Probe Execution (Local Master vs Paramiko SSH)
# ---------------------------------------------------------------------------
def probe_one_server(server: dict) -> dict:
    payload = json.dumps({
        "id": server["id"],
        "name": server["name"],
        "type": server["type"],
        "host": server["host"],
    })
    is_local_master = (
        server["host"] == "103.106.105.77"
        and os.path.exists("/www/wwwroot/pbn-management2.keodinh.net/pbn_matrix.db")
    )
    try:
        if is_local_master:
            proc = subprocess.run(
                ["python3", "-c", REMOTE_PROBE_PY],
                input=payload,
                capture_output=True,
                text=True,
                timeout=180,
            )
            if not proc.stdout.strip():
                raise RuntimeError(proc.stderr.strip() or "Empty stdout from local master probe")
            return json.loads(proc.stdout)

        if paramiko is None:
            raise RuntimeError("paramiko chưa được cài đặt")

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            server["host"],
            port=int(server.get("port") or 22),
            username=server["username"],
            password=server["password"],
            timeout=15,
            banner_timeout=15,
        )
        script_b64 = base64.b64encode(REMOTE_PROBE_PY.encode("utf-8")).decode("ascii")
        cmd = f"python3 -c \"import base64; exec(base64.b64decode('{script_b64}').decode('utf-8'))\""
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=180)
        stdin.write(payload)
        stdin.channel.shutdown_write()
        raw_out = stdout.read().decode("utf-8", errors="replace").strip()
        raw_err = stderr.read().decode("utf-8", errors="replace").strip()
        ssh.close()
        if not raw_out:
            raise RuntimeError(raw_err or "Empty stdout from SSH probe")
        return json.loads(raw_out)
    except Exception as e:
        return {
            "server_id": server["id"],
            "server_name": server["name"],
            "server_host": server["host"],
            "server_type": server["type"],
            "infra": {
                "disk_used_pct": None,
                "mysql_active": None,
                "web_active": None,
                "alerts": [f"Lỗi kết nối/probe server {server['name']} ({server['host']}): {e}"],
            },
            "sites": [],
            "probe_error": str(e),
        }


# ---------------------------------------------------------------------------
# External DNS + HTTP + Redirect + NoIndex + Outbound Links Probe
# ---------------------------------------------------------------------------
def _extract_host(url: str) -> str:
    try:
        return (urllib.parse.urlparse(url).hostname or "").lower().removeprefix("www.")
    except Exception:
        return ""


def audit_http_domain(domain: str, expected_redirect_to: Optional[str] = None) -> Dict[str, Any]:
    clean_domain = domain.replace("http://", "").replace("https://", "").strip().rstrip("/").lower()
    bare_domain = clean_domain.removeprefix("www.")
    expected_host = _extract_host(expected_redirect_to) if expected_redirect_to else ""

    res: Dict[str, Any] = {
        "domain": clean_domain,
        "dns_ip": None,
        "http_status": None,
        "title": None,
        "is_noindex": 0,
        "error_type": "NONE",
        "error_detail": None,
        "screenshot_url": f"https://s0.wp.com/mshots/v1/https%3A%2F%2F{clean_domain}?w=600&h=400",
        "outbound_links": None,
        "redirect_target": None,
    }

    # 1. DNS
    try:
        ip = socket.gethostbyname(clean_domain)
        res["dns_ip"] = ip
        if ip in ("127.0.0.1", "0.0.0.0") or ip.startswith("127."):
            res["error_type"] = "DNS_LOOPBACK"
            res["error_detail"] = f"Domain trỏ về IP {ip} (Chưa trỏ về server thật)"
            return res
    except socket.gaierror:
        res["error_type"] = "DNS_ERROR"
        res["error_detail"] = "Lỗi phân giải tên miền (Chưa trỏ DNS hoặc tên miền chưa trỏ IP)"
        return res
    except Exception as e:
        res["error_type"] = "DNS_ERROR"
        res["error_detail"] = str(e)
        return res

    # 2. HTTP / HTTPS fetch with explicit redirect inspection
    html: Optional[str] = None
    headers = None
    last_err: Optional[str] = None
    final_proto = "https"

    for proto in ("https", "http"):
        cur_url = f"{proto}://{clean_domain}/"
        hops = 0
        got_terminal = False
        while hops < 4:
            hops += 1
            try:
                req = urllib.request.Request(cur_url, headers=HEADERS)
                with _NO_REDIRECT_OPENER.open(req, timeout=8) as resp:
                    res["http_status"] = resp.status
                    headers = resp.headers
                    html = resp.read(262144).decode("utf-8", errors="ignore")
                    final_proto = proto
                    got_terminal = True
                    break
            except urllib.error.HTTPError as e:
                if e.code in (301, 302, 303, 307, 308):
                    loc = e.headers.get("Location", "").strip()
                    next_url = urllib.parse.urljoin(cur_url, loc) if loc else ""
                    target_host = _extract_host(next_url)
                    if target_host and target_host != bare_domain:
                        res["http_status"] = e.code
                        res["redirect_target"] = next_url
                        if expected_host and target_host == expected_host:
                            # Intentional configured 301 redirect
                            res["title"] = f"Redirect -> {target_host}"
                            return res
                        res["error_type"] = "REDIRECT_STRANGE"
                        res["error_detail"] = f"Chuyển hướng {e.code} ra domain lạ: {next_url[:140]}"
                        return res
                    if next_url and next_url != cur_url:
                        cur_url = next_url
                        continue
                res["http_status"] = e.code
                try:
                    html = e.read(65536).decode("utf-8", errors="ignore")
                except Exception:
                    pass
                if e.code in (520, 521, 522, 523, 524):
                    res["error_type"] = "CLOUDFLARE_ERROR"
                    res["error_detail"] = f"Lỗi Cloudflare {e.code} (Web Server Down / Connection Timed Out)"
                    return res
                if e.code == 403:
                    res["error_type"] = "HTTP_403"
                    res["error_detail"] = "Lỗi 403 Forbidden (Firewall chặn hoặc phân quyền thư mục)"
                    return res
                if e.code == 404:
                    res["error_type"] = "HTTP_404"
                    res["error_detail"] = "Lỗi 404 Not Found (Không tìm thấy trang web)"
                    return res
                if e.code >= 500:
                    res["error_type"] = "HTTP_5xx"
                    res["error_detail"] = f"Lỗi máy chủ nội bộ (HTTP {e.code})"
                    return res
                got_terminal = True
                break
            except urllib.error.URLError as e:
                last_err = str(e.reason)
                break
            except Exception as e:
                last_err = str(e)
                break
        if got_terminal:
            break

    if html is None:
        res["error_type"] = "CONN_ERROR"
        low = str(last_err or "").lower()
        if "actively refused" in low or "connection refused" in low:
            res["error_detail"] = "Máy chủ từ chối kết nối (Web server chưa bật hoặc port 80/443 đóng)"
        elif "timed out" in low:
            res["error_detail"] = "Hết thời gian chờ kết nối (Timeout)"
        elif "certificate" in low or "ssl" in low:
            res["error_detail"] = f"Lỗi chứng chỉ SSL: {last_err}"
        else:
            res["error_detail"] = f"Không thể kết nối đến website: {last_err}"
        return res

    # 3. Title & Content Inspection
    t_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    if t_match:
        res["title"] = re.sub(r"\s+", " ", t_match.group(1)).strip()[:100]

    is_noindex = False
    if headers and "noindex" in (headers.get("X-Robots-Tag") or "").lower():
        is_noindex = True
    if re.search(r'<meta[^>]+name=["\']robots["\'][^>]+content=["\'][^"\']*noindex', html, re.I):
        is_noindex = True

    if not is_noindex and res["http_status"] == 200:
        try:
            r_req = urllib.request.Request(f"{final_proto}://{clean_domain}/robots.txt", headers=HEADERS)
            with _NO_REDIRECT_OPENER.open(r_req, timeout=4) as r_resp:
                if r_resp.status == 200:
                    r_txt = r_resp.read(16384).decode("utf-8", errors="ignore")
                    ua_all = False
                    for line in r_txt.splitlines():
                        line = line.split("#", 1)[0].strip()
                        if not line:
                            continue
                        low = line.lower()
                        if low.startswith("user-agent:"):
                            ua_all = (low.split(":", 1)[1].strip() == "*")
                        elif ua_all and low.startswith("disallow:"):
                            if low.split(":", 1)[1].strip() == "/":
                                is_noindex = True
                                break
        except Exception:
            pass

    res["is_noindex"] = 1 if is_noindex else 0

    if "Error establishing a database connection" in html:
        res["error_type"] = "DB_ERROR"
        res["error_detail"] = "Lỗi kết nối cơ sở dữ liệu WordPress (wp-config.php sai thông tin DB)"
    elif "Fatal error:" in html or "Parse error:" in html or "critical error on this website" in html.lower():
        res["error_type"] = "PHP_FATAL"
        res["error_detail"] = "Lỗi nghiêm trọng trong code PHP (Fatal Error)"
    elif any(k in html for k in (
        "Default Web Site Page", "cPanel Default Page",
        "Domain Default page", "Namecheap Parking Page", "Welcome to OpenLiteSpeed"
    )):
        res["error_type"] = "PARKING_PAGE"
        res["error_detail"] = "Trang mặc định của Hosting / Control Panel (Chưa có mã nguồn web)"
    elif len(html.strip()) < 100 and not res["title"]:
        res["error_type"] = "BLANK_PAGE"
        res["error_detail"] = "Trang trắng không có nội dung (White Screen of Death)"
    elif is_noindex:
        res["error_type"] = "NOINDEX"
        res["error_detail"] = "Website đang BẬT chặn Google Index (<meta robots noindex> / robots.txt)"

    # 4. Homepage Outbound Links
    outbound: List[dict] = []
    seen = set()
    for href, anchor_html in re.findall(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.I | re.S):
        href = href.strip()
        if not href.startswith(("http://", "https://")):
            continue
        target_host = _extract_host(href)
        if not target_host or target_host == bare_domain:
            continue
        anchor_text = re.sub(r"<[^>]+>", "", anchor_html).strip() or "[No Anchor]"
        key = (href, anchor_text)
        if key not in seen:
            seen.add(key)
            outbound.append({"url": href, "anchor": anchor_text[:120], "domain": target_host})
    res["outbound_links"] = outbound
    return res


# ---------------------------------------------------------------------------
# Local 9Router AI Classification (http://127.0.0.1:20128/v1, model 9router-1)
# ---------------------------------------------------------------------------
def _get_9router_api_key() -> Optional[str]:
    env_key = os.getenv("NINE_ROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    if env_key:
        return env_key.strip()
    cfg_path = Path("/root/.hermes/config.yaml")
    if cfg_path.exists():
        try:
            txt = cfg_path.read_text(encoding="utf-8", errors="ignore")
            m = re.search(r"api_key:\s*['\"]?([^\s'\"]+)", txt)
            if m:
                return m.group(1).strip()
        except Exception:
            pass
    return None


def classify_with_9router(candidates: List[dict]) -> Dict[str, dict]:
    """
    Sends compact post/file candidates to local 9Router AI (`9router-1`) in small batches.
    Returns mapping `{domain: {"verdict": "SUSPECT"|"OK", "reason": "..."}}`.
    Gracefully returns `{}` if 9Router is unreachable.
    """
    if not candidates:
        return {}
    api_key = _get_9router_api_key()
    if not api_key:
        return {}

    verdicts: Dict[str, dict] = {}
    batch_size = 20
    for i in range(0, min(len(candidates), 80), batch_size):
        batch = candidates[i : i + batch_size]
        prompt = (
            "Bạn là chuyên gia bảo mật WordPress PBN. Hãy phân tích danh sách các bài viết/tệp mới trong 6 ngày gần đây "
            "trên các website PBN (PBN chủ yếu viết tiếng Việt/Anh về thể thao, game bài, casino, bóng đá, tin tức). "
            "Chỉ gắn cờ SUSPECT nếu có dấu hiệu RÕ RÀNG bị hack chèn bài ngoại lai (tiếng Nhật/Trung/Hàn/Nga bất thường, "
            "thuốc kích dục/pharma spam, link ẩn/script tiêm, tác giả lạ đăng bài spam, hoặc tệp mu-plugin lạ khả nghi). "
            "Trả về JSON array thuần (không markdown) dạng: "
            '[{"domain":"example.com","verdict":"OK"|"SUSPECT","reason":"ngắn gọn tiếng Việt"}].\n\n'
            f"Dữ liệu:\n{json.dumps(batch, ensure_ascii=False)}"
        )
        body = json.dumps({
            "model": "9router-1",
            "stream": False,
            "temperature": 0.1,
            "max_tokens": 1200,
            "messages": [{"role": "user", "content": prompt}],
        }).encode("utf-8")
        req = urllib.request.Request(
            "http://127.0.0.1:20128/v1/chat/completions",
            data=body,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        )
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
                content = data["choices"][0]["message"]["content"].strip()
                m = re.search(r"\[.*\]", content, re.S)
                if m:
                    parsed = json.loads(m.group(0))
                    for item in parsed:
                        dom = (item.get("domain") or "").lower().strip()
                        if dom and item.get("verdict") == "SUSPECT":
                            verdicts[dom] = {
                                "verdict": "SUSPECT",
                                "reason": (item.get("reason") or "AI phát hiện bài viết/tệp bất thường")[:180],
                            }
        except Exception:
            continue
    return verdicts


# ---------------------------------------------------------------------------
# Merge SSH + HTTP + AI Findings and Sync to pbn_matrix.db
# ---------------------------------------------------------------------------
def merge_domain_result(
    domain: str,
    http_res: dict,
    wp_res: Optional[dict],
    server_meta: Optional[dict],
    ai_verdict: Optional[dict],
    prev_outbound_domains: set,
) -> dict:
    merged = dict(http_res)
    merged["server_id"] = server_meta.get("server_id") if server_meta else None
    merged["server_name"] = server_meta.get("server_name") if server_meta else None
    merged["server_host"] = server_meta.get("server_host") if server_meta else None

    # NoIndex merged from DB blog_public=0 or physical robots.txt Disallow: /
    db_noindex = False
    if wp_res:
        if wp_res.get("blog_public") == "0" or wp_res.get("robots_disallow"):
            db_noindex = True
            merged["is_noindex"] = 1

    # Outbound link diff vs previous baseline
    cur_out = merged.get("outbound_links") or []
    cur_out_domains = {x.get("domain") for x in cur_out if x.get("domain")}
    new_out_domains = sorted(cur_out_domains - prev_outbound_domains) if prev_outbound_domains else []
    merged["new_outbound_domains"] = new_out_domains

    # Heuristic suspect post check
    suspect_post_reasons: List[str] = []
    if wp_res:
        for p in wp_res.get("recent_posts") or []:
            flags = p.get("flags") or []
            author = (p.get("author") or "").lower()
            if flags:
                suspect_post_reasons.append(f"Bài #{p['id']} ({p['title'][:40]}) có thẻ {', '.join(flags)}")
            elif author and author not in OWNER_ADMIN_WHITELIST:
                suspect_post_reasons.append(f"Bài #{p['id']} ({p['title'][:40]}) do user lạ '{author}' đăng")

    if ai_verdict and ai_verdict.get("verdict") == "SUSPECT":
        suspect_post_reasons.append(f"AI: {ai_verdict.get('reason')}")

    # Filter strange_admins: flag backdoor hex-suffix pattern (_<hex>) or registered <= 14 days
    if wp_res and wp_res.get("strange_admins"):
        cutoff_14d = (datetime.datetime.now() - datetime.timedelta(days=14)).strftime("%Y-%m-%d")
        wp_res["suspect_admins"] = [
            (a.get("login") or "").strip()
            for a in wp_res["strange_admins"]
            if re.search(r"_[0-9a-f]{6,12}$", (a.get("login") or "").strip(), re.I)
            or (a.get("registered") and str(a.get("registered"))[:10] >= cutoff_14d)
        ]

    # Determine highest-priority error_type
    err_type = merged.get("error_type") or "NONE"
    err_detail = merged.get("error_detail")

    if wp_res and wp_res.get("malware_hits"):
        err_type = "MALWARE_DETECTED"
        err_detail = "; ".join(wp_res["malware_hits"][:3])
    elif err_type == "DB_ERROR" or (wp_res and not wp_res.get("db_ok")):
        err_type = "DB_ERROR"
        if wp_res and wp_res.get("db_error") and not err_detail:
            err_detail = f"Lỗi kết nối DB MySQL: {wp_res['db_error']}"
    elif err_type in ("PHP_FATAL", "CLOUDFLARE_ERROR", "HTTP_5xx", "HTTP_403", "HTTP_404", "CONN_ERROR", "DNS_ERROR", "DNS_LOOPBACK", "PARKING_PAGE", "BLANK_PAGE", "REDIRECT_STRANGE"):
        pass
    elif wp_res and wp_res.get("suspect_admins"):
        admins_str = ", ".join(wp_res["suspect_admins"][:5])
        err_type = "WP_STRANGE_ADMIN"
        err_detail = f"Phát hiện user Admin nghi vấn/mới tạo: {admins_str}"
    elif suspect_post_reasons:
        err_type = "WP_SUSPECT_POST"
        err_detail = "; ".join(suspect_post_reasons[:2])
    elif merged["is_noindex"] == 1:
        err_type = "NOINDEX"
        if db_noindex and not err_detail:
            reasons = []
            if wp_res and wp_res.get("blog_public") == "0":
                reasons.append("blog_public=0")
            if wp_res and wp_res.get("robots_disallow"):
                reasons.append("robots.txt Disallow: /")
            err_detail = f"Website đang BẬT chặn Google Index ({', '.join(reasons)})"

    merged["error_type"] = err_type
    merged["error_detail"] = err_detail
    return merged


def sync_to_sqlite(db_path: Path, final_records: List[dict], run_id: str, total_wp_found: int) -> dict:
    conn = sqlite3.connect(str(db_path), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 15000;")

    existing_sites = {r[0].lower(): r[0] for r in conn.execute("SELECT domain FROM sites").fetchall()}
    existing_audits = {r[0].lower(): r[0] for r in conn.execute("SELECT domain FROM site_audits").fetchall()}

    def resolve_key(dom: str) -> str:
        d = dom.lower().strip()
        if d in existing_sites:
            return existing_sites[d]
        if d in existing_audits:
            return existing_audits[d]
        bare = d.removeprefix("www.")
        www = "www." + bare
        for cand in (bare, www):
            if cand in existing_sites:
                return existing_sites[cand]
            if cand in existing_audits:
                return existing_audits[cand]
        return d

    for item in final_records:
        dom = resolve_key(item["domain"])
        conn.execute(
            """
            INSERT INTO site_audits (domain, dns_ip, http_status, title, is_noindex, error_type, error_detail, screenshot_url, audited_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
            ON CONFLICT(domain) DO UPDATE SET
                dns_ip = COALESCE(excluded.dns_ip, site_audits.dns_ip),
                http_status = excluded.http_status,
                title = COALESCE(excluded.title, site_audits.title),
                is_noindex = excluded.is_noindex,
                error_type = excluded.error_type,
                error_detail = excluded.error_detail,
                screenshot_url = excluded.screenshot_url,
                audited_at = datetime('now', 'localtime')
            """,
            (
                dom,
                item.get("dns_ip"),
                item.get("http_status"),
                (item.get("title") or "")[:100] or None,
                1 if item.get("is_noindex") else 0,
                item.get("error_type") or "NONE",
                item.get("error_detail"),
                item.get("screenshot_url"),
            ),
        )
        bare = dom.lower().removeprefix("www.")
        www = "www." + bare
        if item.get("error_type") in ("NONE", "NOINDEX", "WP_STRANGE_ADMIN", "WP_SUSPECT_POST", "MALWARE_DETECTED"):
            conn.execute(
                "UPDATE sites SET is_noindex = ? WHERE lower(domain) IN (?, ?)",
                (1 if item.get("is_noindex") else 0, bare, www),
            )
        if item.get("outbound_links") is not None:
            links = item["outbound_links"]
            conn.execute(
                "UPDATE sites SET total_homepage_links = ?, homepage_outbound_links = ? WHERE lower(domain) IN (?, ?)",
                (len(links), json.dumps(links, ensure_ascii=False), bare, www),
            )

    total = conn.execute("SELECT COUNT(*) FROM site_audits").fetchone()[0]
    noindex_cnt = conn.execute("SELECT COUNT(*) FROM site_audits WHERE is_noindex = 1").fetchone()[0]
    err_cnt = conn.execute("SELECT COUNT(*) FROM site_audits WHERE error_type NOT IN ('NONE', 'NOINDEX')").fetchone()[0]
    healthy_cnt = conn.execute("SELECT COUNT(*) FROM site_audits WHERE error_type = 'NONE' AND is_noindex = 0").fetchone()[0]
    breakdown = {
        r[0]: r[1]
        for r in conn.execute("SELECT error_type, COUNT(*) FROM site_audits WHERE error_type != 'NONE' GROUP BY error_type ORDER BY COUNT(*) DESC").fetchall()
    }
    err_rows = [
        dict(r)
        for r in conn.execute(
            """
            SELECT domain, error_type, error_detail, http_status, title, audited_at
            FROM site_audits
            WHERE error_type NOT IN ('NONE', 'NOINDEX')
            ORDER BY audited_at DESC
            LIMIT 80
            """
        ).fetchall()
    ]
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "timestamp": now_str,
        "run_id": run_id,
        "total_scanned": len(final_records),
        "total_wp_found": total_wp_found,
        "healthy": healthy_cnt,
        "noindex": noindex_cnt,
        "errors": err_cnt,
        "breakdown": breakdown,
        "error_sites": err_rows,
    }
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('LAST_AUDIT_REPORT', ?)", (json.dumps(report, ensure_ascii=False),))
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('LAST_AUDIT_RUN', ?)", (now_str,))
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('LAST_AUDIT_REPORT_UNREAD', '1')")
    conn.execute(
        "INSERT INTO activity_log (site_domain, action, details) VALUES ('cron', 'system_deep_audit_5day', ?)",
        (json.dumps({"run_id": run_id, "scanned": len(final_records), "wp_found": total_wp_found, "errors": err_cnt, "healthy": healthy_cnt}, ensure_ascii=False),),
    )
    conn.commit()
    conn.close()
    return {
        "total_audited": total,
        "healthy": healthy_cnt,
        "noindex": noindex_cnt,
        "errors": err_cnt,
        "breakdown": breakdown,
    }


# ---------------------------------------------------------------------------
# Main Orchestrator
# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description="PBN 5-Day Automated Deep Health Audit (Read-Only)")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="Path to pbn_matrix.db")
    parser.add_argument("--auto-schedule", action="store_true", help="Respect 5-day schedule_state.json gate (today_vn >= next_due_date)")
    parser.add_argument("--force", action="store_true", help="Run immediately ignoring schedule gate")
    parser.add_argument("--dry-run-server", default=None, help="Comma-separated server IDs to test read-only without modifying DB/schedule")
    parser.add_argument("--no-ai", action="store_true", help="Skip 9Router AI triage")
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"[ERROR] Không tìm thấy DB tại {db_path}", file=sys.stderr)
        return 1

    today = today_vn()
    state = load_schedule_state()
    due_date = datetime.date.fromisoformat(state.get("next_due_date") or DEFAULT_FIRST_DUE)

    if args.auto_schedule and not args.force and not args.dry_run_server:
        if today < due_date:
            print(f"[SKIP] {now_vn_str()} VN | today={today.isoformat()} < next_due_date={due_date.isoformat()}")
            return 0

    is_dry_run = bool(args.dry_run_server)
    target_server_ids = None
    if args.dry_run_server:
        target_server_ids = {int(x.strip()) for x in args.dry_run_server.split(",") if x.strip().isdigit()}

    run_id = f"{today.isoformat()}_{datetime.datetime.now(VN_TZ).strftime('%H%M%S')}"
    print(f"[START] PBN Deep Audit run_id={run_id} (dry_run={is_dry_run})")

    # Load servers & existing sites from SQLite
    conn = sqlite3.connect(str(db_path), timeout=15.0)
    conn.row_factory = sqlite3.Row
    servers = [dict(r) for r in conn.execute("SELECT id, name, type, host, port, username, password FROM servers ORDER BY id").fetchall()]
    site_rows = [dict(r) for r in conn.execute("SELECT domain, redirect_to, homepage_outbound_links, status FROM sites").fetchall()]
    conn.close()

    if target_server_ids is not None:
        servers = [s for s in servers if s["id"] in target_server_ids]

    redirect_map: Dict[str, str] = {}
    prev_outbound_map: Dict[str, set] = {}
    db_domains: List[str] = []
    for r in site_rows:
        dom = (r["domain"] or "").strip().lower()
        if not dom or "." not in dom:
            continue
        if r.get("status") != "DELETED":
            db_domains.append(dom)
        if r.get("redirect_to"):
            redirect_map[dom.removeprefix("www.")] = r["redirect_to"]
        if r.get("homepage_outbound_links"):
            try:
                links = json.loads(r["homepage_outbound_links"])
                prev_outbound_map[dom.removeprefix("www.")] = {x.get("domain") for x in links if isinstance(x, dict) and x.get("domain")}
            except Exception:
                pass

    # Load outbound baseline fallback if exists
    if OUTBOUND_BASELINE_PATH.exists():
        try:
            ob_data = json.loads(OUTBOUND_BASELINE_PATH.read_text(encoding="utf-8"))
            for dom, dom_set in ob_data.items():
                prev_outbound_map.setdefault(dom, set(dom_set))
        except Exception:
            pass

    # Step 1: Probe all target servers via SSH/local in parallel
    server_probes: List[dict] = []
    wp_by_domain: Dict[str, dict] = {}
    server_by_domain: Dict[str, dict] = {}
    infra_alerts: List[dict] = []

    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(probe_one_server, srv): srv for srv in servers}
        for fut in as_completed(futs):
            res = fut.result()
            server_probes.append(res)
            alerts = res.get("infra", {}).get("alerts") or []
            if alerts:
                infra_alerts.append({
                    "server_id": res["server_id"],
                    "server_name": res["server_name"],
                    "server_host": res["server_host"],
                    "alerts": alerts,
                })
            for wp in res.get("sites") or []:
                dom = wp["domain"].lower().strip()
                bare = dom.removeprefix("www.")
                wp_by_domain[bare] = wp
                server_by_domain[bare] = {
                    "server_id": res["server_id"],
                    "server_name": res["server_name"],
                    "server_host": res["server_host"],
                }

    total_wp_found = sum(len(p.get("sites") or []) for p in server_probes)
    print(f"[STEP 1] Probed {len(server_probes)} servers, discovered {total_wp_found} WP sites, {len(infra_alerts)} infra alerts.")

    # Step 2: Determine domains for HTTP/DNS audit
    if is_dry_run:
        target_domains = sorted({wp["domain"] for p in server_probes for wp in (p.get("sites") or [])})
    else:
        dom_set = set(db_domains) | {wp["domain"] for p in server_probes for wp in (p.get("sites") or [])}
        target_domains = sorted(dom_set)

    http_by_domain: Dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=25) as ex:
        futs = {
            ex.submit(audit_http_domain, dom, redirect_map.get(dom.removeprefix("www."))): dom
            for dom in target_domains
        }
        for fut in as_completed(futs):
            r = fut.result()
            http_by_domain[r["domain"]] = r

    print(f"[STEP 2] HTTP/DNS audited {len(http_by_domain)} domains.")

    # Step 3: Build AI candidate items & run local 9Router classification
    ai_candidates: List[dict] = []
    recent_posts_summary: List[dict] = []
    extra_mu_summary: List[dict] = []

    for bare, wp in wp_by_domain.items():
        if wp.get("extra_mu_plugins"):
            extra_mu_summary.append({
                "domain": wp["domain"],
                "server": server_by_domain[bare]["server_name"],
                "files": wp["extra_mu_plugins"],
            })
        for p in wp.get("recent_posts") or []:
            entry = {
                "domain": wp["domain"],
                "server": server_by_domain[bare]["server_name"],
                "post_id": p["id"],
                "type": p["type"],
                "title": p["title"][:120],
                "author": p["author"],
                "modified": p["modified"],
                "flags": p["flags"],
                "links": p["links"][:4],
                "snippet": p["snippet"][:180],
            }
            recent_posts_summary.append(entry)
            # Send to 9Router if unusual author, flags, or sample recent posts
            if p["flags"] or (p["author"] and p["author"].lower() not in OWNER_ADMIN_WHITELIST) or len(ai_candidates) < 60:
                ai_candidates.append(entry)

    for item in extra_mu_summary:
        ai_candidates.append({
            "domain": item["domain"],
            "type": "mu_plugin_non_whitelist",
            "files": item["files"],
        })

    ai_verdicts: Dict[str, dict] = {}
    if not args.no_ai and ai_candidates:
        ai_verdicts = classify_with_9router(ai_candidates)
        print(f"[STEP 3] 9Router AI reviewed {len(ai_candidates)} candidates, flagged {len(ai_verdicts)} suspect.")

    # Step 4: Merge findings
    final_records: List[dict] = []
    for dom in target_domains:
        bare = dom.removeprefix("www.")
        hres = http_by_domain[dom]
        wres = wp_by_domain.get(bare)
        smeta = server_by_domain.get(bare)
        aver = ai_verdicts.get(dom) or ai_verdicts.get(bare)
        prev_ob = prev_outbound_map.get(bare, set())
        final_records.append(merge_domain_result(dom, hres, wres, smeta, aver, prev_ob))

    # Build AI review packet
    error_items = [r for r in final_records if r["error_type"] not in ("NONE", "NOINDEX")]
    noindex_items = [r for r in final_records if r["is_noindex"] == 1]
    new_outbound_items = [
        {"domain": r["domain"], "server": r.get("server_name"), "new_domains": r["new_outbound_domains"]}
        for r in final_records if r.get("new_outbound_domains")
    ]

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    if is_dry_run:
        dry_path = REPORT_DIR / "dry_run_test.json"
        dry_summary = {
            "run_id": run_id,
            "servers": [
                {
                    "id": p["server_id"],
                    "name": p["server_name"],
                    "type": p["server_type"],
                    "infra": p["infra"],
                    "wp_count": len(p.get("sites") or []),
                }
                for p in server_probes
            ],
            "total_audited": len(final_records),
            "healthy": sum(1 for r in final_records if r["error_type"] == "NONE" and r["is_noindex"] == 0),
            "noindex": len(noindex_items),
            "errors": len(error_items),
            "recent_posts_count": len(recent_posts_summary),
            "extra_mu_plugins": extra_mu_summary[:20],
            "ai_suspects": ai_verdicts,
            "sample_errors": error_items[:15],
        }
        dry_path.write_text(json.dumps(dry_summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[DRY-RUN DONE] Saved to {dry_path}")
        print(json.dumps({
            "servers": dry_summary["servers"],
            "total_audited": dry_summary["total_audited"],
            "healthy": dry_summary["healthy"],
            "noindex": dry_summary["noindex"],
            "errors": dry_summary["errors"],
            "recent_posts_count": dry_summary["recent_posts_count"],
            "ai_suspects_count": len(ai_verdicts),
        }, ensure_ascii=False, indent=2))
        return 0

    # Step 5: Sync to pbn_matrix.db & save reports
    db_summary = sync_to_sqlite(db_path, final_records, run_id, total_wp_found)

    # Save updated outbound baseline
    new_ob_baseline = {}
    for r in final_records:
        if r.get("outbound_links") is not None:
            bare = r["domain"].removeprefix("www.")
            new_ob_baseline[bare] = sorted({x.get("domain") for x in r["outbound_links"] if x.get("domain")})
    OUTBOUND_BASELINE_PATH.write_text(json.dumps(new_ob_baseline, ensure_ascii=False), encoding="utf-8")

    # Compact packet for OpenMausBot AI morning report
    ai_packet = {
        "run_id": run_id,
        "checked_at_vn": now_vn_str(),
        "ai_reviewed": False,
        "summary": {
            **db_summary,
            "wp_sites_discovered": total_wp_found,
            "servers_probed": len(server_probes),
        },
        "servers": [
            {
                "id": p["server_id"],
                "name": p["server_name"],
                "type": p["server_type"],
                "disk_used_pct": p.get("infra", {}).get("disk_used_pct"),
                "mysql_active": p.get("infra", {}).get("mysql_active"),
                "web_active": p.get("infra", {}).get("web_active"),
                "alerts": p.get("infra", {}).get("alerts") or [],
                "wp_count": len(p.get("sites") or []),
            }
            for p in server_probes
        ],
        "infra_alerts": infra_alerts,
        "error_sites": [
            {
                "domain": r["domain"],
                "server": r.get("server_name"),
                "error_type": r["error_type"],
                "error_detail": r.get("error_detail"),
                "http_status": r.get("http_status"),
            }
            for r in error_items
        ],
        "noindex_sites": [
            {"domain": r["domain"], "server": r.get("server_name"), "error_detail": r.get("error_detail")}
            for r in noindex_items
        ],
        "recent_posts_6d": recent_posts_summary[:120],
        "extra_mu_plugins": extra_mu_summary[:50],
        "new_outbound_links": new_outbound_items[:80],
        "server_9router_suspects": ai_verdicts,
    }
    LATEST_AI_PACKET_PATH.write_text(json.dumps(ai_packet, ensure_ascii=False, indent=2), encoding="utf-8")

    dated_path = REPORT_DIR / f"pbn_deep_report_{today.isoformat()}.json"
    dated_path.write_text(json.dumps(ai_packet, ensure_ascii=False), encoding="utf-8")

    # Advance 5-day schedule state on success
    next_due = today + datetime.timedelta(days=INTERVAL_DAYS)
    save_schedule_state({
        "last_completed_date": today.isoformat(),
        "next_due_date": next_due.isoformat(),
        "interval_days": INTERVAL_DAYS,
        "last_run_id": run_id,
    })

    print(f"[DONE] Synced to DB: {json.dumps(db_summary, ensure_ascii=False)} | next_due_date={next_due.isoformat()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

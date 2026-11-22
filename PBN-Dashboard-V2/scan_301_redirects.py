#!/usr/bin/env python3
"""
PBN Dashboard V2 - Automated 301 Redirect Scanner & Grouper
Scans all sites across HTTP/HTTPS and Cloudflare API to detect, group, and track 301/302 redirects.
Schedule: Run every 2 days via cron.
"""

import os
import sys
import ssl
import json
import time
import sqlite3
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.getenv("DB_PATH", os.path.join(BASE_DIR, "pbn_matrix.db"))

# SSL Context ignoring certificate warnings
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Custom handler that prevents following redirects to capture the HTTP 301/302 response"""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

opener = urllib.request.build_opener(
    urllib.request.HTTPSHandler(context=ssl_ctx),
    urllib.request.HTTPHandler(),
    NoRedirectHandler
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 PBN-Redirect-Auditor/2.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

def check_domain_redirect(domain: str) -> tuple:
    """
    Checks if a domain redirects to an external destination.
    Returns: (domain, redirect_target_or_None)
    """
    clean_d = domain.lower().replace("www.", "").strip().rstrip("/")
    if not clean_d:
        return domain, None

    # Test HTTPS first, fallback to HTTP
    for proto in ["https", "http"]:
        url = f"{proto}://{domain}"
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with opener.open(req, timeout=4.0) as resp:
                # If returns 200 directly without redirect
                if resp.status == 200:
                    return domain, None
        except urllib.error.HTTPError as e:
            if e.code in [301, 302, 307, 308]:
                loc = e.headers.get("Location", "").strip()
                if loc:
                    try:
                        p = urllib.parse.urlparse(loc)
                        target_host = (p.netloc or loc).lower().replace("www.", "").rstrip("/")
                        # Ensure it's redirecting to a DIFFERENT domain (not just http -> https on same domain)
                        if target_host and target_host != clean_d:
                            # Normalize URL
                            if not loc.startswith("http"):
                                loc = f"https://{loc.lstrip('/')}"
                            return domain, loc
                    except Exception:
                        pass
            # Stop after encountering error (403, 500, etc.)
            break
        except Exception:
            continue

    return domain, None

def run_redirect_scan(db_path: str = DB_PATH, max_workers: int = 40):
    start_time = time.time()
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting 301 Redirect Scanner...")
    print(f"Connecting to database: {db_path}")

    if not os.path.exists(db_path):
        print(f"ERROR: Database file {db_path} does not exist!")
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Get all active domains
    sites = [r[0] for r in c.execute("SELECT domain FROM sites WHERE approval_status = 'APPROVED' OR approval_status IS NULL").fetchall()]
    total_sites = len(sites)
    print(f"Loaded {total_sites} domains to check redirects with {max_workers} concurrent workers.")

    redirects_found = {}
    direct_domains = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for domain, target in executor.map(check_domain_redirect, sites):
            if target:
                redirects_found[domain] = target
            else:
                direct_domains.append(domain)

    elapsed = time.time() - start_time
    print(f"Scan finished in {elapsed:.2f}s.")
    print(f"Found {len(redirects_found)} domains with 301/302 Redirects.")
    print(f"Found {len(direct_domains)} domains running directly.")

    # 1. Update redirected domains in database
    for dom, target in redirects_found.items():
        c.execute("UPDATE sites SET redirect_to = ?, updated_at = datetime('now', 'localtime') WHERE domain = ?", (target, dom))

    # 2. Clear redirect_to for domains that are now direct (if previously had redirect_to)
    if direct_domains:
        # Batch in chunks of 500
        for i in range(0, len(direct_domains), 500):
            batch = direct_domains[i:i+500]
            placeholders = ",".join(["?"] * len(batch))
            c.execute(f"UPDATE sites SET redirect_to = NULL WHERE domain IN ({placeholders}) AND redirect_to IS NOT NULL", batch)

    # 3. Log to activity_log
    log_details = json.dumps({
        "total_scanned": total_sites,
        "redirects_count": len(redirects_found),
        "elapsed_seconds": round(elapsed, 1),
        "source": "cron_301_scanner"
    })
    c.execute("""
        INSERT INTO activity_log (action, details, created_at)
        VALUES ('scan_301_redirects', ?, datetime('now', 'localtime'))
    """, (log_details,))

    conn.commit()
    conn.close()
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Successfully synced {len(redirects_found)} 301 redirects into database!")

if __name__ == "__main__":
    db = sys.argv[1] if len(sys.argv) > 1 else DB_PATH
    run_redirect_scan(db)


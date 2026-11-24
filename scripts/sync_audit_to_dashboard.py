"""
Đồng bộ kết quả kiểm tra sức khỏe PBN (JSON từ Đợt 1/2/3 hoặc file gộp)
lên database của Dashboard V2 (https://pbn.keodinh.net/audit) trên 103.106.105.77.

Hỗ trợ đọc một hoặc nhiều file JSON có dạng:
  {
    "checked_at": "2026-11-26 16:00:00",
    "sites": [
      {
        "domain": "example.com",
        "dns_ip": "1.2.3.4",
        "http_status": 200,
        "title": "Trang chu",
        "is_noindex": 0,
        "error_type": "NONE",
        "error_detail": null,
        "outbound_links": [...]   // tùy chọn
      }
    ]
  }
Hoặc truyền trực tiếp danh sách site trong key "results" / list top-level.
"""

import argparse
import json
import sys
from pathlib import Path
import paramiko

MASTER_HOST = "103.106.105.77"
MASTER_USER = "root"
MASTER_PASS = "q9icdLH1!*0B"
REMOTE_DB = "/www/wwwroot/pbn-management2.keodinh.net/pbn_matrix.db"

REMOTE_SYNC_PY = r'''
import json, sqlite3, sys, datetime

payload = json.load(sys.stdin)
db_path = payload["db_path"]
records = payload["records"]
dry_run = payload.get("dry_run", False)
update_report = payload.get("update_report", True)

conn = sqlite3.connect(db_path, timeout=20.0)
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA journal_mode = WAL;")
conn.execute("PRAGMA busy_timeout = 10000;")

existing_sites = {r[0].lower(): r[0] for r in conn.execute("SELECT domain FROM sites").fetchall()}
existing_audits = {r[0].lower(): r[0] for r in conn.execute("SELECT domain FROM site_audits").fetchall()}

def resolve_domain_key(dom):
    d = dom.replace("http://", "").replace("https://", "").strip().rstrip("/").lower()
    if d in existing_sites:
        return existing_sites[d]
    if d in existing_audits:
        return existing_audits[d]
    bare = d[4:] if d.startswith("www.") else d
    www = "www." + bare
    for cand in (bare, www):
        if cand in existing_sites:
            return existing_sites[cand]
        if cand in existing_audits:
            return existing_audits[cand]
    return d

updated = 0
for item in records:
    raw_dom = (item.get("domain") or "").strip()
    if not raw_dom:
        continue
    domain = resolve_domain_key(raw_dom)
    dns_ip = item.get("dns_ip")
    http_status = item.get("http_status")
    title = (item.get("title") or "")[:100] or None
    is_noindex = 1 if item.get("is_noindex") else 0
    error_type = (item.get("error_type") or "NONE").strip() or "NONE"
    error_detail = item.get("error_detail")
    if error_type == "NONE" and is_noindex == 1:
        error_type = "NOINDEX"
    if error_type == "NOINDEX" and not error_detail:
        error_detail = "Website đang BẬT chặn Google Index (blog_public=0 / noindex)"
    screenshot_url = item.get("screenshot_url") or f"https://s0.wp.com/mshots/v1/https%3A%2F%2F{domain}?w=600&h=400"

    if not dry_run:
        conn.execute("""
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
        """, (domain, dns_ip, http_status, title, is_noindex, error_type, error_detail, screenshot_url))

        bare = domain.lower().replace("www.", "")
        www = "www." + bare
        if error_type in ("NONE", "NOINDEX"):
            conn.execute("UPDATE sites SET is_noindex = ? WHERE lower(domain) IN (?, ?)", (is_noindex, bare, www))

        if item.get("outbound_links") is not None:
            links = item["outbound_links"]
            conn.execute(
                "UPDATE sites SET total_homepage_links = ?, homepage_outbound_links = ? WHERE lower(domain) IN (?, ?)",
                (len(links), json.dumps(links, ensure_ascii=False), bare, www)
            )
    updated += 1

total = conn.execute("SELECT COUNT(*) FROM site_audits").fetchone()[0]
noindex_cnt = conn.execute("SELECT COUNT(*) FROM site_audits WHERE is_noindex = 1").fetchone()[0]
err_cnt = conn.execute("SELECT COUNT(*) FROM site_audits WHERE error_type NOT IN ('NONE', 'NOINDEX')").fetchone()[0]
healthy_cnt = conn.execute("SELECT COUNT(*) FROM site_audits WHERE error_type = 'NONE' AND is_noindex = 0").fetchone()[0]
breakdown = {
    r[0]: r[1]
    for r in conn.execute("SELECT error_type, COUNT(*) FROM site_audits WHERE error_type != 'NONE' GROUP BY error_type ORDER BY COUNT(*) DESC").fetchall()
}

if not dry_run and update_report:
    err_rows = [dict(r) for r in conn.execute("""
        SELECT domain, error_type, error_detail, http_status, title, audited_at
        FROM site_audits
        WHERE error_type NOT IN ('NONE', 'NOINDEX')
        ORDER BY audited_at DESC
        LIMIT 50
    """).fetchall()]
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "timestamp": now_str,
        "total_scanned": updated if updated > 0 else total,
        "healthy": healthy_cnt,
        "noindex": noindex_cnt,
        "errors": err_cnt,
        "breakdown": breakdown,
        "error_sites": err_rows,
    }
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('LAST_AUDIT_REPORT', ?)", (json.dumps(report, ensure_ascii=False),))
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('LAST_AUDIT_RUN', ?)", (now_str,))
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('LAST_AUDIT_REPORT_UNREAD', '1')", ())
    conn.execute(
        "INSERT INTO activity_log (site_domain, action, details) VALUES ('cron', 'system_audit_scan', ?)",
        (json.dumps({"scanned": updated, "errors": err_cnt, "healthy": healthy_cnt, "source": "scheduled_5day_sync"}, ensure_ascii=False),)
    )

if not dry_run:
    conn.commit()
conn.close()

print(json.dumps({
    "dry_run": dry_run,
    "synced_records": updated,
    "summary": {
        "total_audited": total,
        "healthy": healthy_cnt,
        "noindex": noindex_cnt,
        "errors": err_cnt,
        "breakdown": breakdown
    }
}, ensure_ascii=False))
'''


def load_records(paths):
    merged = {}
    for p in paths:
        data = json.loads(Path(p).read_text(encoding="utf-8"))
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get("sites") or data.get("results") or []
        else:
            items = []
        for item in items:
            if isinstance(item, dict) and item.get("domain"):
                merged[item["domain"].strip().lower()] = item
    return list(merged.values())


if __name__ == "__main__":
    import base64
    parser = argparse.ArgumentParser(description="Sync PBN health check JSON to Dashboard V2 /audit DB")
    parser.add_argument("files", nargs="*", help="JSON batch files")
    parser.add_argument("--dry-run", action="store_true", help="Read summary without modifying DB")
    parser.add_argument("--no-report", action="store_true", help="Skip updating LAST_AUDIT_REPORT/LAST_AUDIT_RUN")
    args = parser.parse_args()

    records = load_records(args.files) if args.files else []
    payload = {
        "db_path": REMOTE_DB,
        "records": records,
        "dry_run": args.dry_run,
        "update_report": not args.no_report,
    }
    script_b64 = base64.b64encode(REMOTE_SYNC_PY.encode("utf-8")).decode("ascii")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(MASTER_HOST, username=MASTER_USER, password=MASTER_PASS, timeout=15)
    stdin, stdout, stderr = ssh.exec_command(f"python3 -c \"import base64; exec(base64.b64decode('{script_b64}').decode())\"")
    stdin.write(json.dumps(payload, ensure_ascii=False))
    stdin.channel.shutdown_write()
    out = stdout.read().decode("utf-8", errors="replace").strip()
    err = stderr.read().decode("utf-8", errors="replace").strip()
    ssh.close()
    if err:
        print(err, file=sys.stderr)
    print(out)
    if not out:
        sys.exit(1)

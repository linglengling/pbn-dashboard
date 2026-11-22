import sqlite3
import json
import datetime
from typing import Optional, List, Dict, Any
from .config import DB_PATH
from .auth import hash_password

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    return conn

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. users
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                role TEXT DEFAULT 'admin',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Admin default user
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            h, s = hash_password("Abcd@12347")
            cursor.execute("INSERT INTO users (username, password_hash, salt, role) VALUES (?, ?, ?, ?)", ("admin", h, s, "admin"))

        # 2. servers
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS servers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                host TEXT NOT NULL,
                port INTEGER DEFAULT 22,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                status TEXT DEFAULT 'ONLINE',
                sites_count INTEGER DEFAULT 0,
                last_checked DATETIME,
                error_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 3. sites
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sites (
                domain TEXT PRIMARY KEY,
                ip TEXT,
                last_seen DATETIME,
                status TEXT DEFAULT 'ONLINE',
                cluster TEXT,
                api_key TEXT,
                site_url TEXT,
                wp_version TEXT,
                total_homepage_links INTEGER DEFAULT 0,
                head_code TEXT,
                homepage_outbound_links TEXT,
                approval_status TEXT DEFAULT 'APPROVED',
                server_id INTEGER,
                server_host TEXT,
                redirect_to TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME
            )
        """)
        
        # Check if redirect_to, updated_at, is_noindex columns exist (migration)
        site_cols = [c[1] for c in cursor.execute("PRAGMA table_info(sites)").fetchall()]
        if "redirect_to" not in site_cols:
            cursor.execute("ALTER TABLE sites ADD COLUMN redirect_to TEXT;")
        if "updated_at" not in site_cols:
            cursor.execute("ALTER TABLE sites ADD COLUMN updated_at DATETIME;")
        if "is_noindex" not in site_cols:
            cursor.execute("ALTER TABLE sites ADD COLUMN is_noindex INTEGER DEFAULT 0;")
        if "screenshot_url" not in site_cols:
            cursor.execute("ALTER TABLE sites ADD COLUMN screenshot_url TEXT;")

        # Clusters Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clusters (
                name TEXT PRIMARY KEY,
                color TEXT DEFAULT '#38bdf8',
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            INSERT OR IGNORE INTO clusters (name)
            SELECT DISTINCT cluster FROM sites WHERE cluster IS NOT NULL AND cluster != ''
        """)

        # 4. backlinks
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS backlinks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_domain TEXT NOT NULL,
                target_url TEXT NOT NULL,
                anchor_text TEXT NOT NULL,
                post_id INTEGER,
                post_url TEXT,
                status TEXT DEFAULT 'ACTIVE',
                last_verified DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 5. posts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_domain TEXT NOT NULL,
                wp_post_id INTEGER,
                post_title TEXT,
                post_url TEXT,
                status TEXT DEFAULT 'PUBLISHED',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 6. activity_log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_domain TEXT,
                action TEXT,
                details TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 7. settings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # 8. site_audits
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS site_audits (
                domain TEXT PRIMARY KEY,
                dns_ip TEXT,
                http_status INTEGER,
                title TEXT,
                is_noindex INTEGER DEFAULT 0,
                error_type TEXT DEFAULT 'NONE',
                error_detail TEXT,
                screenshot_url TEXT,
                audited_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Indexes for fast lookup
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_domain ON posts(site_domain);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_backlinks_domain ON backlinks(site_domain);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sites_approval ON sites(approval_status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sites_server_id ON sites(server_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audits_noindex ON site_audits(is_noindex);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audits_err ON site_audits(error_type);")
        conn.commit()

# --- USERS ---
def get_user_by_username(username: str) -> Optional[dict]:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        return dict(row) if row else None

def get_user_by_id(user_id: int) -> Optional[dict]:
    with get_db() as conn:
        row = conn.execute("SELECT id, username, role, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None

# --- SITES ---
def get_sites(include_pending: bool = False, server_id: Optional[int] = None) -> List[dict]:
    with get_db() as conn:
        query = """
            SELECT s.domain, s.ip, s.last_seen, s.status, s.cluster, s.api_key, s.site_url, 
                   s.wp_version, s.total_homepage_links, s.homepage_outbound_links, s.approval_status, 
                   s.server_id, s.server_host, s.redirect_to, s.is_noindex, s.created_at,
                   COALESCE(s.screenshot_url, a.screenshot_url) AS screenshot_url
            FROM sites s
            LEFT JOIN site_audits a ON s.domain = a.domain
        """
        clauses = []
        params = []
        if not include_pending:
            clauses.append("(s.approval_status = 'APPROVED' OR s.approval_status IS NULL)")
        if server_id is not None:
            clauses.append("s.server_id = ?")
            params.append(server_id)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY s.last_seen DESC"
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

def get_pending_sites() -> List[dict]:
    with get_db() as conn:
        rows = conn.execute("""
            SELECT s.domain, s.ip, s.last_seen, s.status, s.cluster, s.api_key, s.site_url, 
                   s.wp_version, s.total_homepage_links, s.homepage_outbound_links, s.approval_status, 
                   s.server_id, s.server_host, s.redirect_to, s.created_at,
                   COALESCE(s.screenshot_url, a.screenshot_url) AS screenshot_url
            FROM sites s
            LEFT JOIN site_audits a ON s.domain = a.domain
            WHERE s.approval_status = 'PENDING' 
            ORDER BY s.last_seen DESC
        """).fetchall()
        return [dict(r) for r in rows]

def get_site_detail(domain: str) -> Optional[dict]:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM sites WHERE domain = ?", (domain,)).fetchone()
        return dict(row) if row else None

def approve_sites(domains: List[str]):
    with get_db() as conn:
        placeholders = ",".join(["?"] * len(domains))
        conn.execute(f"UPDATE sites SET approval_status = 'APPROVED', status = 'ONLINE' WHERE domain IN ({placeholders})", domains)
        conn.commit()

def reject_sites(domains: List[str], delete_permanently: bool = False):
    with get_db() as conn:
        placeholders = ",".join(["?"] * len(domains))
        if delete_permanently:
            conn.execute(f"DELETE FROM sites WHERE domain IN ({placeholders})", domains)
        else:
            conn.execute(f"UPDATE sites SET approval_status = 'REJECTED', status = 'OFFLINE' WHERE domain IN ({placeholders})", domains)
        conn.commit()

def record_site_ping(data: dict) -> dict:
    domain = data.get("domain", "").strip()
    if not domain:
        return {"success": False, "error": "Missing domain"}
    
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        existing = conn.execute("SELECT domain, approval_status FROM sites WHERE domain = ?", (domain,)).fetchone()
        
        outbound_str = data.get("homepage_outbound_links")
        if isinstance(outbound_str, (list, dict)):
            outbound_str = json.dumps(outbound_str)

        # Update is_noindex if blog_public is provided
        blog_public = data.get("blog_public")
        is_noindex_clause = ""
        is_noindex_val = None
        if blog_public is not None:
            is_noindex_val = 1 if int(blog_public) == 0 else 0
            is_noindex_clause = ", is_noindex = ?"

        if not existing:
            conn.execute("""
                INSERT INTO sites (domain, ip, last_seen, status, cluster, api_key, site_url, 
                                  wp_version, total_homepage_links, head_code, homepage_outbound_links, 
                                  approval_status, server_host, is_noindex, created_at)
                VALUES (?, ?, ?, 'ONLINE', ?, ?, ?, ?, ?, ?, ?, 'APPROVED', ?, ?, ?)
            """, (
                domain, data.get("ip") or data.get("server_ip"), now, data.get("cluster"),
                data.get("api_key"), data.get("site_url") or f"https://{domain}",
                data.get("wp_version"), data.get("total_homepage_links", 0),
                data.get("head_code"), outbound_str, data.get("server_ip"),
                is_noindex_val if is_noindex_val is not None else 0, now
            ))
            conn.commit()
            return {"success": True, "action": "created_approved", "domain": domain}
        else:
            # Website đang gửi ping thành công -> Chắc chắn đang ONLINE!
            # Tự động duyệt APPROVED nếu đang ở PENDING hoặc chưa duyệt
            approval_status = 'REJECTED' if existing["approval_status"] == 'REJECTED' else 'APPROVED'
            if is_noindex_val is not None:
                conn.execute("""
                    UPDATE sites SET 
                        last_seen = ?, status = 'ONLINE', ip = COALESCE(?, ip),
                        approval_status = ?,
                        total_homepage_links = COALESCE(?, total_homepage_links),
                        head_code = COALESCE(?, head_code),
                        homepage_outbound_links = COALESCE(?, homepage_outbound_links),
                        is_noindex = ?,
                        updated_at = ?
                    WHERE domain = ?
                """, (
                    now, data.get("ip") or data.get("server_ip"),
                    approval_status,
                    data.get("total_homepage_links"), data.get("head_code"),
                    outbound_str, is_noindex_val, now, domain
                ))
            else:
                conn.execute("""
                    UPDATE sites SET 
                        last_seen = ?, status = 'ONLINE', ip = COALESCE(?, ip),
                        approval_status = ?,
                        total_homepage_links = COALESCE(?, total_homepage_links),
                        head_code = COALESCE(?, head_code),
                        homepage_outbound_links = COALESCE(?, homepage_outbound_links),
                        updated_at = ?
                    WHERE domain = ?
                """, (
                    now, data.get("ip") or data.get("server_ip"),
                    approval_status,
                    data.get("total_homepage_links"), data.get("head_code"),
                    outbound_str, now, domain
                ))
            conn.commit()
            return {"success": True, "action": "updated", "domain": domain, "approval_status": approval_status}

# --- SERVERS ---
def get_all_servers() -> List[dict]:
    with get_db() as conn:
        rows = conn.execute("""
            SELECT id, name, type, host, port, username, password, status, sites_count, last_checked, error_message, created_at 
            FROM servers ORDER BY id ASC
        """).fetchall()
        return [dict(r) for r in rows]

def get_server_by_id(server_id: int) -> Optional[dict]:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM servers WHERE id = ?", (server_id,)).fetchone()
        return dict(row) if row else None

def create_server(data: dict) -> int:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO servers (name, type, host, port, username, password, status, sites_count)
            VALUES (?, ?, ?, ?, ?, ?, 'ONLINE', 0)
        """, (
            data.get("name"), data.get("type", "vps"), data.get("host"),
            int(data.get("port", 22)), data.get("username"), data.get("password")
        ))
        conn.commit()
        return cursor.lastrowid

def update_server(server_id: int, data: dict):
    with get_db() as conn:
        fields = []
        params = []
        for k in ["name", "type", "host", "port", "username", "password", "status"]:
            if k in data:
                fields.append(f"{k} = ?")
                params.append(data[k])
        if fields:
            params.append(server_id)
            conn.execute(f"UPDATE servers SET {', '.join(fields)} WHERE id = ?", params)
            conn.commit()

def delete_server(server_id: int):
    with get_db() as conn:
        conn.execute("DELETE FROM servers WHERE id = ?", (server_id,))
        conn.execute("UPDATE sites SET server_id = NULL WHERE server_id = ?", (server_id,))
        conn.commit()

# --- STATS ---
def get_stats() -> dict:
    with get_db() as conn:
        c = conn.cursor()
        total_domains = c.execute("SELECT COUNT(*) FROM sites WHERE approval_status = 'APPROVED' OR approval_status IS NULL").fetchone()[0]
        online_sites = c.execute("SELECT COUNT(*) FROM sites WHERE (approval_status = 'APPROVED' OR approval_status IS NULL) AND status = 'ONLINE'").fetchone()[0]
        offline_sites = total_domains - online_sites
        pending_sites = c.execute("SELECT COUNT(*) FROM sites WHERE approval_status = 'PENDING'").fetchone()[0]
        active_backlinks = c.execute("SELECT COUNT(*) FROM backlinks WHERE status = 'ACTIVE'").fetchone()[0]
        total_posts = c.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
        total_servers = c.execute("SELECT COUNT(*) FROM servers").fetchone()[0]
        host_websites = c.execute("SELECT COALESCE(SUM(sites_count), 0) FROM servers").fetchone()[0]
        total_301 = c.execute("SELECT COUNT(*) FROM sites WHERE redirect_to IS NOT NULL AND redirect_to != ''").fetchone()[0]

        return {
            "totalDomains": total_domains,
            "totalSites": total_domains,
            "hostWebsites": host_websites,
            "total301": total_301,
            "onlineSites": online_sites,
            "offlineSites": offline_sites,
            "pendingSites": pending_sites,
            "activeBacklinks": active_backlinks,
            "totalPosts": total_posts,
            "totalServers": total_servers
        }

# --- BACKLINKS ---
def get_all_backlinks() -> List[dict]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM backlinks ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]

def insert_backlink(site_domain: str, target_url: str, anchor_text: str, post_id: int = None, post_url: str = None) -> int:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO backlinks (site_domain, target_url, anchor_text, post_id, post_url, status)
            VALUES (?, ?, ?, ?, ?, 'ACTIVE')
        """, (site_domain, target_url, anchor_text, post_id, post_url))
        conn.commit()
        return cursor.lastrowid

def delete_backlink(backlink_id: int):
    with get_db() as conn:
        conn.execute("DELETE FROM backlinks WHERE id = ?", (backlink_id,))
        conn.commit()

# --- POSTS ---
def get_all_posts(limit: int = 100) -> List[dict]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM posts ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

def create_post_record(site_domain: str, wp_post_id: int, post_title: str, post_url: str) -> int:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO posts (site_domain, wp_post_id, post_title, post_url, status)
            VALUES (?, ?, ?, ?, 'PUBLISHED')
        """, (site_domain, wp_post_id, post_title, post_url))
        conn.commit()
        return cursor.lastrowid

# --- ACTIVITY LOG ---
def log_activity(target: str, action: str, details: Any = None):
    with get_db() as conn:
        detail_str = json.dumps(details, ensure_ascii=False) if isinstance(details, (dict, list)) else str(details or '')
        conn.execute("INSERT INTO activity_log (site_domain, action, details) VALUES (?, ?, ?)", (target, action, detail_str))
        conn.commit()

def get_activity_logs(limit: int = 100) -> List[dict]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM activity_log ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

# --- SETTINGS ---
def get_settings() -> dict:
    with get_db() as conn:
        rows = conn.execute("SELECT key, value FROM settings").fetchall()
        return {r["key"]: r["value"] for r in rows}

def set_setting(key: str, value: str):
    with get_db() as conn:
        conn.execute("INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = ?", (key, value, value))
        conn.commit()

# --- CLUSTERS ---
def get_clusters() -> List[dict]:
    with get_db() as conn:
        cursor = conn.cursor()
        rows = cursor.execute("""
            SELECT c.name, COALESCE(c.color, '#38bdf8') as color, c.description, c.created_at,
                   COUNT(s.domain) as site_count
            FROM clusters c
            LEFT JOIN sites s ON s.cluster = c.name
            GROUP BY c.name
            ORDER BY site_count DESC, c.name ASC
        """).fetchall()
        
        result = [dict(r) for r in rows]
        existing_names = set(r["name"] for r in result)

        # Include orphan clusters if any
        orphan_rows = cursor.execute("""
            SELECT cluster as name, '#38bdf8' as color, NULL as description, NULL as created_at,
                   COUNT(domain) as site_count
            FROM sites
            WHERE cluster IS NOT NULL AND cluster != ''
            GROUP BY cluster
        """).fetchall()
        for orow in orphan_rows:
            if orow["name"] not in existing_names:
                result.append(dict(orow))
                cursor.execute("INSERT OR IGNORE INTO clusters (name) VALUES (?)", (orow["name"],))
                conn.commit()

        # Always ensure 'default' cluster exists
        if "default" not in existing_names and not any(r["name"] == "default" for r in result):
            cursor.execute("INSERT OR IGNORE INTO clusters (name, color) VALUES ('default', '#94a3b8')")
            conn.commit()
            result.append({"name": "default", "color": "#94a3b8", "description": "Cụm mặc định", "site_count": 0})

        return result

def create_or_get_cluster(name: str, color: Optional[str] = None, description: Optional[str] = None) -> str:
    name = name.strip()
    if not name:
        raise ValueError("Tên cluster không được để trống")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO clusters (name, color, description)
            VALUES (?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                color = COALESCE(?, color),
                description = COALESCE(?, description)
        """, (name, color or '#38bdf8', description, color, description))
        conn.commit()
    return name

def delete_cluster(name: str):
    name = name.strip()
    with get_db() as conn:
        conn.execute("UPDATE sites SET cluster = 'default' WHERE cluster = ?", (name,))
        conn.execute("DELETE FROM clusters WHERE name = ?", (name,))
        conn.commit()

def update_sites_cluster(domains: List[str], cluster_name: str, color: Optional[str] = None):
    cluster_name = cluster_name.strip()
    if not cluster_name:
        raise ValueError("Tên cluster không được để trống")

    create_or_get_cluster(cluster_name, color=color)

    clean_domains = []
    for d in domains:
        if not d:
            continue
        cleaned = d.lower().strip()
        cleaned = cleaned.replace("https://", "").replace("http://", "").split("/")[0].strip()
        if cleaned:
            clean_domains.append(cleaned)

    clean_domains = list(dict.fromkeys(clean_domains))
    if not clean_domains:
        return 0, []

    with get_db() as conn:
        cursor = conn.cursor()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        placeholders = ",".join("?" for _ in clean_domains)
        cursor.execute(f"""
            UPDATE sites 
            SET cluster = ?, updated_at = ?
            WHERE domain IN ({placeholders})
        """, [cluster_name, now, *clean_domains])
        updated_count = cursor.rowcount
        conn.commit()

        for d in clean_domains[:10]:
            log_activity(d, "cluster_updated", {"new_cluster": cluster_name})

    return updated_count, clean_domains


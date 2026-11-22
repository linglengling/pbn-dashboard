const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const crypto = require('crypto');

const dbPath = path.resolve(__dirname, 'pbn_matrix.db');
const db = new sqlite3.Database(dbPath);

// Tối ưu hóa SQLite cho dữ liệu lớn & Đọc/Ghi đồng thời (High Performance Tuning)
db.exec(`
    PRAGMA journal_mode = WAL;
    PRAGMA synchronous = NORMAL;
    PRAGMA busy_timeout = 5000;
`);

// Helper mã hóa mật khẩu PBKDF2
const hashPassword = (password, salt) => {
    if (!salt) salt = crypto.randomBytes(16).toString('hex');
    const hash = crypto.pbkdf2Sync(password, salt, 1000, 64, 'sha512').toString('hex');
    return { hash, salt };
};

// ============================================================
// DATABASE SCHEMA & INDEXES
// ============================================================
db.serialize(() => {
    // Bảng lưu tài khoản đăng nhập Dashboard (User Management)
    db.run(`
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            role TEXT DEFAULT 'admin',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    `, () => {
        // Tự động khởi tạo hoặc cập nhật mật khẩu cho tài khoản admin: Abcd@12347
        const { hash, salt } = hashPassword('Abcd@12347');
        db.get("SELECT * FROM users WHERE username = 'admin'", (err, row) => {
            if (!err && !row) {
                db.run("INSERT INTO users (username, password_hash, salt, role) VALUES (?, ?, ?, ?)", ['admin', hash, salt, 'admin']);
                console.log('[INIT] Admin user created: admin / Abcd@12347');
            } else if (!err && row) {
                db.run("UPDATE users SET password_hash = ?, salt = ? WHERE username = 'admin'", [hash, salt]);
                console.log('[INIT] Admin password updated to Abcd@12347');
            }
        });
    });
    // Bảng lưu trạng thái của 200 site
    db.run(`
        CREATE TABLE IF NOT EXISTS sites (
            domain TEXT PRIMARY KEY,
            ip TEXT,
            last_seen DATETIME,
            status TEXT DEFAULT 'OFFLINE',
            cluster TEXT,
            api_key TEXT,
            site_url TEXT,
            wp_version TEXT,
            total_homepage_links INTEGER DEFAULT 0,
            head_code TEXT,
            homepage_outbound_links TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    `);

    // Đảm bảo cột total_homepage_links tồn tại trên database cũ
    db.run("ALTER TABLE sites ADD COLUMN total_homepage_links INTEGER DEFAULT 0", (err) => {
        // Bỏ qua lỗi nếu cột đã tồn tại
    });

    // Đảm bảo cột head_code tồn tại trên database cũ
    db.run("ALTER TABLE sites ADD COLUMN head_code TEXT", (err) => {
        // Bỏ qua lỗi nếu cột đã tồn tại
    });

    // Đảm bảo cột homepage_outbound_links tồn tại trên database cũ
    db.run("ALTER TABLE sites ADD COLUMN homepage_outbound_links TEXT", (err) => {
        // Bỏ qua lỗi nếu cột đã tồn tại
    });

    // Đảm bảo cột paragraph_html tồn tại trên database cũ
    db.run("ALTER TABLE backlinks ADD COLUMN paragraph_html TEXT", (err) => {
        // Bỏ qua lỗi nếu cột đã tồn tại
    });

    // Đảm bảo cột server_ip tồn tại trên database
    db.run("ALTER TABLE sites ADD COLUMN server_ip TEXT", (err) => {
        // Bỏ qua lỗi nếu cột đã tồn tại
    });

    // Đảm bảo cột server_id và server_host tồn tại trên database
    db.run("ALTER TABLE sites ADD COLUMN server_id INTEGER", (err) => {});
    db.run("ALTER TABLE sites ADD COLUMN server_host TEXT", (err) => {});

    // Đảm bảo cột approval_status tồn tại (mặc định APPROVED cho các site đã có)
    db.run("ALTER TABLE sites ADD COLUMN approval_status TEXT DEFAULT 'APPROVED'", (err) => {
        // Bỏ qua lỗi nếu cột đã tồn tại
    });

    // Bảng lưu danh sách Server / VPS / cPanel
    db.run(`
        CREATE TABLE IF NOT EXISTS servers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL DEFAULT 'vps',
            host TEXT NOT NULL UNIQUE,
            port INTEGER DEFAULT 22,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            auth_type TEXT DEFAULT 'password',
            status TEXT DEFAULT 'ONLINE',
            sites_count INTEGER DEFAULT 0,
            last_checked DATETIME,
            error_message TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    `, () => {
        // Tự động khởi tạo 8 server ban đầu nếu chưa có
        const initialServers = [
            { name: "VPS aaPanel 1", type: "vps", host: "194.233.83.83", port: 22, username: "root", password: "E^@r8&R6~NFo/!" },
            { name: "VPS aaPanel 2", type: "vps", host: "172.96.190.231", port: 22, username: "root", password: "BkUEwvB9QavrrfEmfbah" },
            { name: "VPS aaPanel 3", type: "vps", host: "198.252.110.104", port: 22, username: "root", password: "kzIM1OysATQMdi9MogDd" },
            { name: "VPS aaPanel 4", type: "vps", host: "198.252.101.160", port: 22, username: "root", password: "pi6W0HbBOJjqcYL1Q3Yn" },
            { name: "VPS aaPanel 5", type: "vps", host: "198.252.99.79", port: 22, username: "root", password: "rv0xH9UazYoUFfgwu3bC" },
            { name: "cPanel SNG-SD120", type: "cpanel", host: "sng-sd120.arandomserver.com", port: 22, username: "mseocom2", password: "23eM])Ba4xMM6g" },
            { name: "cPanel DAL-SD201", type: "cpanel", host: "dal-sd201.arandomserver.com", port: 22, username: "mseocom", password: "c+uI5x55T1eZJ-" },
            { name: "cPanel TOR-SD204", type: "cpanel", host: "tor-sd204.arandomserver.com", port: 22, username: "mseocom1", password: "hf0A*CC4J5-g1f" }
        ];

        initialServers.forEach(srv => {
            db.run(`
                INSERT INTO servers (name, type, host, port, username, password, status)
                VALUES (?, ?, ?, ?, ?, ?, 'ONLINE')
                ON CONFLICT(host) DO UPDATE SET
                    name = excluded.name,
                    type = excluded.type,
                    port = excluded.port,
                    username = excluded.username,
                    password = excluded.password
            `, [srv.name, srv.type, srv.host, srv.port, srv.username, srv.password]);
        });
    });

    // Bảng lưu backlink đã chèn trên từng site
    db.run(`
        CREATE TABLE IF NOT EXISTS backlinks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_domain TEXT,
            target_url TEXT,
            anchor_text TEXT,
            location TEXT DEFAULT 'post',
            post_id INTEGER,
            paragraph_html TEXT,
            status TEXT DEFAULT 'active',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (site_domain) REFERENCES sites(domain)
        )
    `);

    // Bảng lưu bài viết đã đăng trên từng site
    db.run(`
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_domain TEXT,
            wp_post_id INTEGER,
            title TEXT,
            status TEXT DEFAULT 'published',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (site_domain) REFERENCES sites(domain)
        )
    `);

    // Bảng log hoạt động
    db.run(`
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_domain TEXT,
            action TEXT,
            details TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    `);

    // Bảng lưu Hồ sơ RAG / Tone / Persona của từng site vệ tinh
    db.run(`
        CREATE TABLE IF NOT EXISTS site_profiles (
            domain TEXT PRIMARY KEY,
            tone TEXT DEFAULT 'Informative & Professional',
            brand TEXT DEFAULT '',
            logo_url TEXT DEFAULT '',
            language TEXT DEFAULT 'vi',
            persona TEXT DEFAULT 'SEO Expert',
            forbidden_terms TEXT DEFAULT '',
            custom_instructions TEXT DEFAULT '',
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    `);
    // Ensure logo_url column exists if table was created previously
    db.run(`ALTER TABLE site_profiles ADD COLUMN logo_url TEXT DEFAULT ''`, () => {});

    // Bảng lưu bộ nhớ RAG bài viết đã tạo để tránh trùng lặp
    db.run(`
        CREATE TABLE IF NOT EXISTS rag_memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_domain TEXT,
            keyword TEXT,
            title TEXT,
            summary TEXT,
            outline_json TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    `);

    // Bảng lưu lịch sử tác vụ OpenClaw Task Manager
    db.run(`
        CREATE TABLE IF NOT EXISTS openclaw_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT UNIQUE NOT NULL,
            command TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            response TEXT DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            completed_at DATETIME
        )
    `);

    // Tối ưu hóa Index giúp tra cứu siêu tốc khi số lượng bài viết lên hàng ngàn/hàng chục ngàn
    db.run(`CREATE INDEX IF NOT EXISTS idx_rag_keyword ON rag_memories(keyword);`);
    db.run(`CREATE INDEX IF NOT EXISTS idx_rag_domain ON rag_memories(site_domain);`);
    db.run(`CREATE INDEX IF NOT EXISTS idx_posts_domain ON posts(site_domain);`);
    db.run(`CREATE INDEX IF NOT EXISTS idx_posts_wpid ON posts(wp_post_id);`);
    db.run(`CREATE INDEX IF NOT EXISTS idx_backlinks_domain ON backlinks(site_domain);`);
    db.run(`CREATE INDEX IF NOT EXISTS idx_backlinks_target ON backlinks(target_url);`);

    // Bảng lưu cấu hình AI và cài đặt chung
    db.run(`
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    `, () => {
        // Khởi tạo các giá trị cấu hình AI mặc định
        const defaults = {
            'ai_provider': 'openai',
            'ai_api_key': '',
            'ai_api_base': 'https://api.openai.com/v1',
            'ai_model': 'gpt-4o',
            'ai_seo_prompt': 'Write a highly optimized, comprehensive, and engaging SEO article based on the keyword "{keyword}". Use clean HTML formatting (only using p, h2, h3, ul, ol, li, strong, em, and standard img tags). Include an engaging title in <h1> (this will be used as the post title, do not put h1 in the content body though, only returning it at the top as <h1>Title</h1>), a brief introduction, multiple structured sections using h2/h3, and a logical conclusion. Ensure the content is 100% unique, reads naturally, and flows well. Randomly insert 1-2 high-quality context images from Unsplash matching the topic using HTML img tags (e.g. <img src="https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=800&q=80" alt="beautiful natural scenery">). Keep other text blocks standard. The language of the article must match the language of the keyword.',
            'ai_rewrite_prompt': 'You are an expert SEO copywriter. Re-write the following article/content to make it 100% unique, highly engaging, and optimized for search engines. Retain all original outbound links (a tags) and original image URLs (img tags) if any, but rewrite all paragraphs, headings, and structure completely in clean HTML. Start your response with the title in <h1> (e.g. <h1>New Optimized Title</h1>), followed by the rewritten content in HTML tags. Content to rewrite:\n\n{content}',
            'ai_use_history_chain': 'false',
            'ai_history_chain_prompt': 'Write another completely unique, high-quality, and highly engaging article on the same topic/keyword. Avoid any similarity in structure, heading titles, paragraph layouts, subtopics, or wording with the previous articles in our conversation history. Make it read naturally, use clean HTML (only p, h2, h3, ul, ol, li, strong, em, and img). Start your response with the new title in <h1>, followed by the article content. Do not repeat the same topics, examples, or intro hooks mentioned in the previous turns.'
        };
        for (const [key, val] of Object.entries(defaults)) {
            db.run("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", [key, val]);
        }
    });
});

// ============================================================
// HELPER: Promisify db methods
// ============================================================
const dbAll = (sql, params = []) => {
    return new Promise((resolve, reject) => {
        db.all(sql, params, (err, rows) => {
            if (err) reject(err);
            else resolve(rows || []);
        });
    });
};

const dbRun = (sql, params = []) => {
    return new Promise((resolve, reject) => {
        db.run(sql, params, function (err) {
            if (err) reject(err);
            else resolve({ lastID: this.lastID, changes: this.changes });
        });
    });
};

const dbGet = (sql, params = []) => {
    return new Promise((resolve, reject) => {
        db.get(sql, params, (err, row) => {
            if (err) reject(err);
            else resolve(row);
        });
    });
};

// ============================================================
// SITES
// ============================================================
const getSites = (includePending = false) => {
    if (includePending) {
        return dbAll("SELECT * FROM sites ORDER BY last_seen DESC");
    }
    return dbAll("SELECT * FROM sites WHERE approval_status = 'APPROVED' OR approval_status IS NULL ORDER BY last_seen DESC");
};

const getPendingSites = () => {
    return dbAll("SELECT * FROM sites WHERE approval_status = 'PENDING' ORDER BY last_seen DESC");
};

const getSite = (domain) => dbGet("SELECT * FROM sites WHERE domain = ?", [domain]);

const updateSite = (domain, ip, cluster, siteUrl, apiKey, totalHomepageLinks, headCode, homepageOutboundLinks, serverIp = null) => {
    return dbRun(`
        INSERT INTO sites (domain, ip, server_ip, last_seen, status, approval_status, cluster, site_url, api_key, total_homepage_links, head_code, homepage_outbound_links)
        VALUES (?, ?, ?, datetime('now','localtime'), 'PENDING', 'PENDING', ?, ?, ?, ?, ?, ?)
        ON CONFLICT(domain) DO UPDATE SET
            ip = excluded.ip,
            server_ip = COALESCE(excluded.server_ip, sites.server_ip, excluded.ip),
            last_seen = excluded.last_seen,
            status = CASE WHEN sites.approval_status = 'APPROVED' OR sites.approval_status IS NULL THEN 'ONLINE' ELSE sites.status END,
            cluster = COALESCE(excluded.cluster, sites.cluster),
            site_url = COALESCE(excluded.site_url, sites.site_url),
            api_key = COALESCE(excluded.api_key, sites.api_key),
            total_homepage_links = COALESCE(excluded.total_homepage_links, sites.total_homepage_links),
            head_code = COALESCE(excluded.head_code, sites.head_code),
            homepage_outbound_links = COALESCE(excluded.homepage_outbound_links, sites.homepage_outbound_links)
    `, [domain, ip, serverIp || ip, cluster, siteUrl, apiKey, totalHomepageLinks || 0, headCode || '', homepageOutboundLinks || '[]']);
};

const approveSite = (domain) => {
    return dbRun("UPDATE sites SET approval_status = 'APPROVED', status = 'ONLINE' WHERE domain = ?", [domain]);
};

const bulkApproveSites = (domains) => {
    if (!Array.isArray(domains) || domains.length === 0) return Promise.resolve({ changes: 0 });
    const placeholders = domains.map(() => '?').join(',');
    return dbRun(`UPDATE sites SET approval_status = 'APPROVED', status = 'ONLINE' WHERE domain IN (${placeholders})`, domains);
};

const rejectSite = (domain) => {
    return dbRun("UPDATE sites SET approval_status = 'REJECTED', status = 'OFFLINE' WHERE domain = ?", [domain]);
};

const bulkRejectSites = (domains) => {
    if (!Array.isArray(domains) || domains.length === 0) return Promise.resolve({ changes: 0 });
    const placeholders = domains.map(() => '?').join(',');
    return dbRun(`UPDATE sites SET approval_status = 'REJECTED', status = 'OFFLINE' WHERE domain IN (${placeholders})`, domains);
};

const deleteSite = (domain) => {
    return dbRun("DELETE FROM sites WHERE domain = ?", [domain]);
};

const bulkDeleteSites = (domains) => {
    if (!Array.isArray(domains) || domains.length === 0) return Promise.resolve({ changes: 0 });
    const placeholders = domains.map(() => '?').join(',');
    return dbRun(`DELETE FROM sites WHERE domain IN (${placeholders})`, domains);
};

const updateSiteHeadCode = (domain, headCode) => {
    return dbRun("UPDATE sites SET head_code = ? WHERE domain = ?", [headCode, domain]);
};

const registerSite = (domain, apiKey, cluster = 'default', siteUrl = '') => {
    return dbRun(`
        INSERT INTO sites (domain, api_key, cluster, site_url, status, approval_status)
        VALUES (?, ?, ?, ?, 'OFFLINE', 'APPROVED')
        ON CONFLICT(domain) DO UPDATE SET
            api_key = excluded.api_key,
            cluster = COALESCE(excluded.cluster, sites.cluster),
            site_url = COALESCE(excluded.site_url, sites.site_url),
            approval_status = 'APPROVED'
    `, [domain, apiKey, cluster, siteUrl || `http://${domain}`]);
};

const markSiteOffline = (domain) => {
    return dbRun("UPDATE sites SET status = 'OFFLINE' WHERE domain = ?", [domain]);
};

const getOnlineSites = () => dbAll("SELECT * FROM sites WHERE status = 'ONLINE'");

const getStaleSites = (minutesThreshold = 30) => {
    return dbAll(`
        SELECT * FROM sites
        WHERE status = 'ONLINE'
        AND last_seen < datetime('now','localtime','-${minutesThreshold} minutes')
    `);
};

// ============================================================
// BACKLINKS
// ============================================================
const addBacklink = (siteDomain, targetUrl, anchorText, location, postId, paragraphHtml) => {
    return dbRun(
        "INSERT INTO backlinks (site_domain, target_url, anchor_text, location, post_id, paragraph_html) VALUES (?, ?, ?, ?, ?, ?)",
        [siteDomain, targetUrl, anchorText, location, postId || null, paragraphHtml || '']
    );
};

const getBacklinks = (siteDomain) => {
    if (siteDomain) {
        return dbAll("SELECT * FROM backlinks WHERE site_domain = ? ORDER BY created_at DESC", [siteDomain]);
    }
    return dbAll("SELECT * FROM backlinks ORDER BY created_at DESC");
};

const removeBacklink = (id) => {
    return dbRun("UPDATE backlinks SET status = 'removed' WHERE id = ?", [id]);
};

const killSwitchBacklinks = (siteDomain) => {
    return dbRun("UPDATE backlinks SET status = 'removed' WHERE site_domain = ? AND status = 'active'", [siteDomain]);
};

const killSwitchByCluster = (cluster) => {
    return dbRun(`
        UPDATE backlinks SET status = 'removed'
        WHERE site_domain IN (SELECT domain FROM sites WHERE cluster = ?)
        AND status = 'active'
    `, [cluster]);
};

// ============================================================
// POSTS
// ============================================================
const addPost = (siteDomain, wpPostId, title) => {
    return dbRun(
        "INSERT INTO posts (site_domain, wp_post_id, title) VALUES (?, ?, ?)",
        [siteDomain, wpPostId, title]
    );
};

const getPosts = (siteDomain) => {
    if (siteDomain) {
        return dbAll("SELECT * FROM posts WHERE site_domain = ? ORDER BY created_at DESC", [siteDomain]);
    }
    return dbAll("SELECT * FROM posts ORDER BY created_at DESC");
};

// ============================================================
// ACTIVITY LOG
// ============================================================
const logActivity = (siteDomain, action, details) => {
    return dbRun(
        "INSERT INTO activity_log (site_domain, action, details) VALUES (?, ?, ?)",
        [siteDomain, action, typeof details === 'string' ? details : JSON.stringify(details)]
    );
};

const getActivityLog = (limit = 50) => {
    return dbAll("SELECT * FROM activity_log ORDER BY created_at DESC LIMIT ?", [limit]);
};

const getActivityLogWithPagination = async (options = {}) => {
    const page = Math.max(1, parseInt(options.page) || 1);
    const limit = Math.max(10, Math.min(500, parseInt(options.limit) || 50));
    const offset = (page - 1) * limit;

    let whereClause = "WHERE 1=1";
    const params = [];

    if (options.action && options.action.trim()) {
        whereClause += " AND LOWER(action) LIKE ?";
        params.push(`%${options.action.trim().toLowerCase()}%`);
    }

    if (options.month && options.month.trim()) {
        whereClause += " AND strftime('%Y-%m', created_at) = ?";
        params.push(options.month.trim());
    }

    if (options.search && options.search.trim()) {
        const q = `%${options.search.trim().toLowerCase()}%`;
        whereClause += " AND (LOWER(site_domain) LIKE ? OR LOWER(details) LIKE ? OR LOWER(action) LIKE ?)";
        params.push(q, q, q);
    }

    const countRow = await dbGet(`SELECT COUNT(*) as total FROM activity_log ${whereClause}`, params);
    const totalCount = countRow ? countRow.total : 0;
    const totalPages = Math.ceil(totalCount / limit) || 1;

    const dataSql = `SELECT * FROM activity_log ${whereClause} ORDER BY created_at DESC LIMIT ? OFFSET ?`;
    const data = await dbAll(dataSql, [...params, limit, offset]);

    return {
        data,
        totalCount,
        totalPages,
        currentPage: page,
        limit
    };
};

const getAvailableLogMonths = async () => {
    const rows = await dbAll(`
        SELECT DISTINCT strftime('%Y-%m', created_at) as month 
        FROM activity_log 
        WHERE created_at IS NOT NULL 
        ORDER BY month DESC
    `);
    return rows.map(r => r.month).filter(Boolean);
};

const pruneActivityLog = (daysToKeep = 30) => {
    const days = parseInt(daysToKeep) || 30;
    return dbRun("DELETE FROM activity_log WHERE created_at < datetime('now', '-' || ? || ' days')", [days]);
};

const clearAllActivityLog = () => {
    return dbRun("DELETE FROM activity_log");
};

// ============================================================
// STATS
// ============================================================
const getStats = async () => {
    const total = await dbGet("SELECT COUNT(*) as count FROM sites WHERE approval_status = 'APPROVED' OR approval_status IS NULL");
    const online = await dbGet("SELECT COUNT(*) as count FROM sites WHERE (approval_status = 'APPROVED' OR approval_status IS NULL) AND status = 'ONLINE'");
    const offline = await dbGet("SELECT COUNT(*) as count FROM sites WHERE (approval_status = 'APPROVED' OR approval_status IS NULL) AND status = 'OFFLINE'");
    const pending = await dbGet("SELECT COUNT(*) as count FROM sites WHERE approval_status = 'PENDING'");
    const activeLinks = await dbGet("SELECT COUNT(*) as count FROM backlinks WHERE status = 'active'");
    const totalPosts = await dbGet("SELECT COUNT(*) as count FROM posts");
    const totalServers = await dbGet("SELECT COUNT(*) as count FROM servers");
    return {
        totalSites: total.count,
        onlineSites: online.count,
        offlineSites: offline.count,
        pendingSites: pending.count,
        activeBacklinks: activeLinks.count,
        totalPosts: totalPosts.count,
        totalServers: totalServers ? totalServers.count : 0
    };
};

const updateClustersBulk = (domains, cluster) => {
    if (!Array.isArray(domains) || domains.length === 0) return Promise.resolve({ changes: 0 });
    const placeholders = domains.map(() => '?').join(',');
    return dbRun(`
        UPDATE sites SET cluster = ?
        WHERE domain IN (${placeholders})
    `, [cluster, ...domains]);
};

const getSettings = async () => {
    const rows = await dbAll("SELECT * FROM settings");
    const config = {};
    rows.forEach(r => { config[r.key] = r.value; });
    return config;
};

const getSetting = async (key) => {
    const row = await dbGet("SELECT value FROM settings WHERE key = ?", [key]);
    return row ? row.value : null;
};

const saveSettings = async (settingsObj) => {
    for (const [key, value] of Object.entries(settingsObj)) {
        await dbRun("INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value", [key, value]);
    }
    return true;
};

const deletePost = (id) => {
    return dbRun("DELETE FROM posts WHERE id = ?", [id]);
};

// ============================================================
// SITE PROFILES (RAG & TONE PERSONA)
// ============================================================
const getSiteProfile = (domain) => {
    return dbGet("SELECT * FROM site_profiles WHERE domain = ?", [domain]);
};

const saveSiteProfile = (domain, data) => {
    const { tone, brand, logo_url, language, persona, forbidden_terms, custom_instructions } = data;
    return dbRun(`
        INSERT INTO site_profiles (domain, tone, brand, logo_url, language, persona, forbidden_terms, custom_instructions, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
        ON CONFLICT(domain) DO UPDATE SET
            tone = excluded.tone,
            brand = excluded.brand,
            logo_url = excluded.logo_url,
            language = excluded.language,
            persona = excluded.persona,
            forbidden_terms = excluded.forbidden_terms,
            custom_instructions = excluded.custom_instructions,
            updated_at = datetime('now','localtime')
    `, [domain, tone || 'Informative & Professional', brand || '', logo_url || '', language || 'vi', persona || 'SEO Expert', forbidden_terms || '', custom_instructions || '']);
};

const getAllSiteProfiles = () => {
    return dbAll("SELECT * FROM site_profiles");
};

// ============================================================
// RAG MEMORIES (HISTORY AVOIDANCE)
// ============================================================
const searchRagMemories = (keyword, excludeDomain = null) => {
    if (!keyword) return Promise.resolve([]);
    const kw = `%${keyword.trim().toLowerCase()}%`;
    if (excludeDomain) {
        return dbAll(
            "SELECT * FROM rag_memories WHERE (LOWER(keyword) LIKE ? OR LOWER(title) LIKE ?) AND site_domain != ? ORDER BY created_at DESC LIMIT 10",
            [kw, kw, excludeDomain]
        );
    }
    return dbAll(
        "SELECT * FROM rag_memories WHERE LOWER(keyword) LIKE ? OR LOWER(title) LIKE ? ORDER BY created_at DESC LIMIT 10",
        [kw, kw]
    );
};

const saveRagMemory = (siteDomain, keyword, title, summary = '', outlineJson = '') => {
    return dbRun(
        "INSERT INTO rag_memories (site_domain, keyword, title, summary, outline_json) VALUES (?, ?, ?, ?, ?)",
        [siteDomain, keyword, title, summary, typeof outlineJson === 'string' ? outlineJson : JSON.stringify(outlineJson)]
    );
};

// ============================================================
// USER MANAGEMENT (AUTHENTICATION & CRUD)
// ============================================================
const getUserByUsername = (username) => {
    if (!username) return Promise.resolve(null);
    return dbGet("SELECT * FROM users WHERE LOWER(username) = ?", [username.trim().toLowerCase()]);
};

const getUserById = (id) => {
    return dbGet("SELECT id, username, role, created_at FROM users WHERE id = ?", [id]);
};

const getAllUsers = () => {
    return dbAll("SELECT id, username, role, created_at FROM users ORDER BY created_at ASC");
};

const createUser = (username, password, role = 'admin') => {
    const { hash, salt } = hashPassword(password);
    return dbRun(
        "INSERT INTO users (username, password_hash, salt, role) VALUES (?, ?, ?, ?)",
        [username.trim().toLowerCase(), hash, salt, role]
    );
};

const updateUserPassword = (id, newPassword) => {
    const { hash, salt } = hashPassword(newPassword);
    return dbRun(
        "UPDATE users SET password_hash = ?, salt = ? WHERE id = ?",
        [hash, salt, id]
    );
};

const deleteUser = (id) => {
    return dbRun("DELETE FROM users WHERE id = ?", [id]);
};

const verifyPassword = (password, user) => {
    if (!user || !user.password_hash || !user.salt) return false;
    const { hash } = hashPassword(password, user.salt);
    return hash === user.password_hash;
};

// ============================================================
// OPENCLAW TASK MANAGER HELPERS
// ============================================================
const addOpenClawTask = (taskId, command) => {
    return dbRun("INSERT INTO openclaw_tasks (task_id, command, status) VALUES (?, ?, 'pending')", [taskId, command]);
};

const updateOpenClawTask = (taskId, status, response = '') => {
    const resStr = typeof response === 'string' ? response : JSON.stringify(response);
    return dbRun(
        "UPDATE openclaw_tasks SET status = ?, response = ?, completed_at = datetime('now','localtime') WHERE task_id = ?",
        [status, resStr, taskId]
    );
};

const getOpenClawTasks = (limit = 50) => {
    return dbAll("SELECT * FROM openclaw_tasks ORDER BY created_at DESC LIMIT ?", [limit]);
};

// ============================================================
// SERVER / VPS / CPANEL MANAGEMENT
// ============================================================
const getAllServers = () => {
    return dbAll("SELECT id, name, type, host, port, username, password, status, sites_count, last_checked, error_message, created_at FROM servers ORDER BY id ASC");
};

const getServerById = (id) => {
    return dbGet("SELECT * FROM servers WHERE id = ?", [id]);
};

const createServer = ({ name, type, host, port, username, password }) => {
    return dbRun(
        "INSERT INTO servers (name, type, host, port, username, password, status) VALUES (?, ?, ?, ?, ?, ?, 'ONLINE')",
        [name, type || 'vps', host.trim(), parseInt(port) || 22, username.trim(), password]
    );
};

const updateServer = (id, { name, type, host, port, username, password }) => {
    let sql = "UPDATE servers SET name = ?, type = ?, host = ?, port = ?, username = ?, updated_at = datetime('now','localtime')";
    let params = [name, type, host.trim(), parseInt(port) || 22, username.trim()];
    if (password) {
        sql += ", password = ?";
        params.push(password);
    }
    sql += " WHERE id = ?";
    params.push(id);
    return dbRun(sql, params);
};

const deleteServer = (id) => {
    return dbRun("DELETE FROM servers WHERE id = ?", [id]);
};

const updateServerStatus = (id, status, sitesCount = null, errorMessage = null) => {
    let sql = "UPDATE servers SET status = ?, last_checked = datetime('now','localtime'), error_message = ?";
    let params = [status, errorMessage];
    if (sitesCount !== null && sitesCount !== undefined) {
        sql += ", sites_count = ?";
        params.push(sitesCount);
    }
    sql += " WHERE id = ?";
    params.push(id);
    return dbRun(sql, params);
};

module.exports = {
    db, dbAll, dbRun, dbGet,
    getSites, getPendingSites, getSite, updateSite, registerSite,
    approveSite, bulkApproveSites, rejectSite, bulkRejectSites, deleteSite, bulkDeleteSites,
    markSiteOffline, getOnlineSites, getStaleSites,
    addBacklink, getBacklinks, removeBacklink,
    killSwitchBacklinks, killSwitchByCluster,
    addPost, getPosts, deletePost,
    logActivity, getActivityLog, getActivityLogWithPagination, getAvailableLogMonths, pruneActivityLog, clearAllActivityLog,
    getStats,
    updateClustersBulk,
    updateSiteHeadCode,
    getSettings, getSetting, saveSettings,
    getSiteProfile, saveSiteProfile, getAllSiteProfiles,
    searchRagMemories, saveRagMemory,
    getUserByUsername, getUserById, getAllUsers, createUser, updateUserPassword, deleteUser, verifyPassword,
    addOpenClawTask, updateOpenClawTask, getOpenClawTasks,
    getAllServers, getServerById, createServer, updateServer, deleteServer, updateServerStatus
};

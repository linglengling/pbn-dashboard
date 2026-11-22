#!/usr/bin/env python3
# =========================================================
# Reset theme, fix malware, clean root PHP
# Install / reset plugins (mu-plugins + optional)
# Hard reset WP Core:
#   - XÓA SẠCH VÀ THAY MỚI TOÀN BỘ FILE CORE (index.php, wp-login.php, wp-load.php,...)
#   - QUÉT VÀ CÁCH LY 100% FILE LẠ / FILE RÁC / FILE NGHI MÃ ĐỘC Ở ROOT (.bak, .old, không đuôi, file lạ)
#   - XÓA SẠCH VÀ CÀI MỚI 100% THƯ MỤC MU-PLUGINS
# Lock root / secure permissions
# Export CSV report
# cPanel VERSION (Supports non-root user & root)
# =========================================================

import os
import sys
import subprocess
import datetime
import csv
import shutil

# =========================================================
# CONFIG & STATE
# =========================================================
REPORT = []

# =========================================================
# PLUGINS
# =========================================================
LOCAL_INIT_CANDIDATES = [
    os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "mu-plugins", "init.php")),
    os.path.expanduser("~/mu-plugins/init.php"),
    "/www/wwwroot/pbn-management2.keodinh.net/mu-plugins/init.php",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "init.php"),
]

OPTIONAL_PLUGINS = [
    {
        "name": "Rank Math SEO",
        "url": "http://cdn.keodinh.net/wp/wp-seo-rank-math.tar.gz?ss=77",
        "slug": "wp-seo-rank-math"
    }
]

# =========================================================
# WHITELISTS
# =========================================================
WP_ROOT_CORE_PHP = [
    "index.php", "wp-activate.php", "wp-blog-header.php",
    "wp-comments-post.php", "wp-cron.php", "wp-links-opml.php",
    "wp-load.php", "wp-login.php", "wp-mail.php", "wp-settings.php",
    "wp-signup.php", "wp-trackback.php", "xmlrpc.php"
]

WP_ROOT_PHP_WHITELIST = set(WP_ROOT_CORE_PHP) | {"wp-config.php"}

EXTRA_ROOT_PHP_WHITELIST = {
    "aios-bootstrap.php", "wordfence-waf.php",
    "wp-cache.php", "advanced-cache.php", "object-cache.php",
}

ROOT_FILE_WHITELIST = {
    ".htaccess",
    "license.txt",
    "readme.html",
    "robots.txt",
    "sitemap.xml",
    "sitemap_index.xml",
    "ads.txt",
}

SAFE_HIDDEN_FILES = {
    ".user.ini",
    ".well-known",
    ".litespeed_flag",
}

# =========================================================
# HELPER FUNCTIONS
# =========================================================
def log(msg, indent=0, level="INFO"):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [{level}] {' '*indent}{msg}", flush=True)

def run(cmd, cwd=None):
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    stdout = result.stdout.decode('utf-8', errors='replace')
    stderr = result.stderr.decode('utf-8', errors='replace')
    return stdout, stderr

def is_root():
    return hasattr(os, "geteuid") and os.geteuid() == 0

def unlock_all(root):
    log("Unlock toàn bộ file (chattr / chmod)", 4, "DEBUG")
    if is_root():
        run(f"chattr -i -R '{root}' 2>/dev/null")
    run(f"chmod -R u+w '{root}' 2>/dev/null")

# =========================================================
# WP-CLI HELPER (cPanel friendly)
# =========================================================
def get_wp_cli():
    out, _ = run("which wp 2>/dev/null")
    sys_wp = out.strip()
    if sys_wp and os.path.isfile(sys_wp):
        return sys_wp
    
    home = os.path.expanduser("~")
    local_cli = os.path.join(home, "wp-cli.phar")
    if not os.path.isfile(local_cli):
        log("Tải wp-cli.phar về thư mục home...", 6, "DEBUG")
        run(f"curl -s -o '{local_cli}' https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar")
        run(f"chmod +x '{local_cli}'")
    return f"php {local_cli}"

def wp(root, cmd):
    cli = get_wp_cli()
    allow_root = "--allow-root" if is_root() else ""
    return run(f"{cli} {cmd} --path='{root}' {allow_root}")

# =========================================================
# HARD RESET WORDPRESS CORE (XÓA SẠCH VÀ CÀI MỚI 100%)
# =========================================================
def prepare_wp_core_cache():
    """Tải và giải nén WP Core mới nhất vào /tmp đúng 1 lần cho toàn bộ server"""
    tmp = "/tmp/wp-core-clean"
    tar_path = f"{tmp}/latest.tar.gz"
    wp_src = f"{tmp}/wordpress"

    if os.path.isdir(wp_src) and os.path.isfile(f"{wp_src}/wp-settings.php"):
        return wp_src

    run(f"rm -rf '{tmp}' && mkdir -p '{tmp}'")
    log("Tải WordPress core mới nhất từ wordpress.org (dùng chung toàn server)...", 2)
    run(f"wget -q -O '{tar_path}' https://wordpress.org/latest.tar.gz")
    run(f"tar -xzf '{tar_path}' -C '{tmp}'")
    
    if os.path.isdir(wp_src) and os.path.isfile(f"{wp_src}/wp-settings.php"):
        log("✅ Tải và giải nén WP core mẫu thành công", 2)
        return wp_src
    else:
        log("❌ Lỗi khi tải hoặc giải nén WordPress core!", 2, "ERROR")
        return None

def hard_reset_wp_core(root, wp_src):
    """
    1. XÓA SẠCH HOÀN TOÀN: wp-admin, wp-includes
    2. XÓA HẲN các file PHP core ở ROOT: index.php, wp-login.php, wp-load.php, v.v.
    3. Copy đè 100% bộ file core WordPress mới từ nguồn chuẩn
    """
    if not wp_src or not os.path.isdir(wp_src):
        log("Bỏ qua hard reset WP core do thiếu nguồn core hợp lệ", 4, "WARNING")
        return

    log("HARD RESET WordPress CORE: Xóa sạch core cũ & thay mới 100%", 4)
    
    # 1. Xóa sạch hoàn toàn 2 thư mục core chính
    run(f"rm -rf '{root}/wp-admin' '{root}/wp-includes'")
    
    # 2. XÓA HẲN TỪNG FILE PHP core ở ROOT (kể cả index.php)
    for cpf in WP_ROOT_CORE_PHP:
        target_file = os.path.join(root, cpf)
        if os.path.exists(target_file):
            run(f"rm -f '{target_file}'")

    # 3. Sao chép toàn bộ core WordPress mới 100% vào root
    run(f"cp -a '{wp_src}/wp-admin' '{root}/'")
    run(f"cp -a '{wp_src}/wp-includes' '{root}/'")
    run(f"find '{wp_src}' -maxdepth 1 -type f -name '*.php' ! -name 'wp-config-sample.php' -exec cp -f {{}} '{root}/' \\;")
    log("✅ Đã xóa và cài mới 100% WordPress core (bao gồm index.php và toàn bộ file root)", 6)

# =========================================================
# DỌN SẠCH FILE LẠ / FILE RÁC / FILE NGHI MALWARE Ở ROOT
# =========================================================
def clean_suspicious_root_files(root):
    """
    Quét và cách ly tất cả các file rác, file backup (.bak, .bk, .old, .sql, .zip),
    file không extension, error_log hoặc file lạ ở ROOT vào wp-content/malware/root-files/
    """
    log("Quét & dọn sạch file rác / nghi malware ở ROOT (.bak, .old, error_log, file không đuôi...)", 4)
    dest = f"{root}/wp-content/malware/root-files"
    os.makedirs(dest, exist_ok=True)

    out, _ = run(f"find '{root}' -maxdepth 1 -type f")
    moved = []

    for f in out.splitlines():
        f = f.strip()
        if not f:
            continue
        name = os.path.basename(f)

        # Bỏ qua whitelist chuẩn
        if name in ROOT_FILE_WHITELIST:
            continue
        if name in SAFE_HIDDEN_FILES or name.startswith(".well-known"):
            continue
        if name in WP_ROOT_PHP_WHITELIST or name in EXTRA_ROOT_PHP_WHITELIST:
            continue
        if name.endswith(".php"):
            continue  # Đã có hàm move_suspicious_root_php xử lý riêng

        # Kiểm tra file rác, file backup hoặc file không có đuôi mở rộng
        ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
        is_junk_or_suspicious = (
            "." not in name or # Không có đuôi mở rộng (ví dụ: __HB__, radio, malware script...)
            ext in {"bak", "bk", "old", "orig", "sql", "zip", "tar", "gz", "rar", "7z", "log", "tmp"} or
            name.startswith(".htaccess.bak") or
            name.startswith("wp-config.php.bak") or
            name == "error_log" or
            ext not in {"html", "txt", "css", "js", "ico", "png", "jpg", "jpeg", "webp", "ini", "svg"}
        )

        if is_junk_or_suspicious:
            run(f"mv '{f}' '{dest}/{name}'")
            moved.append(name)
            log(f"  [Đã cách ly file rác/lạ ở ROOT]: {name}", 6, "INFO")

    return moved

def move_suspicious_root_php(root):
    """
    Quét và cách ly tất cả các file PHP lạ ở ROOT (không thuộc danh sách WordPress Core chuẩn)
    vào wp-content/malware/root-php/
    """
    log("Quét & cách ly file PHP lạ ở ROOT (không thuộc WordPress Core chuẩn)", 4)
    moved = []
    whitelist = WP_ROOT_PHP_WHITELIST | EXTRA_ROOT_PHP_WHITELIST
    dest = f"{root}/wp-content/malware/root-php"
    os.makedirs(dest, exist_ok=True)

    out, _ = run(f"find '{root}' -maxdepth 1 -type f -name '*.php'")

    for f in out.splitlines():
        f = f.strip()
        if not f:
            continue
        name = os.path.basename(f)
        if name in whitelist:
            continue

        run(f"mv '{f}' '{dest}/{name}'")
        moved.append(name)
        log(f"  [Đã cách ly PHP lạ ở ROOT]: {name}", 6, "WARNING")

    return moved

# =========================================================
# MU-PLUGINS (XÓA SẠCH CŨ VÀ CÀI MỚI 100%)
# =========================================================
def install_mu_plugins(root):
    """
    Xóa sạch hoàn toàn thư mục wp-content/mu-plugins cũ để diệt mọi backdoor/malware,
    chỉ bảo lưu p-manager.php rồi cài mới 100% mu-plugins từ CDN.
    """
    log("Xóa sạch & cài lại MU-PLUGINS mới 100%", 4)
    wp_content = f"{root}/wp-content"
    mu_dir = f"{wp_content}/mu-plugins"

    # 1. Bảo lưu file kết nối p-manager.php (nếu có) sang /tmp
    pmanager_path = f"{mu_dir}/p-manager.php"
    has_pmanager = os.path.isfile(pmanager_path)
    pmanager_backup = f"/tmp/p-manager-backup-{os.path.basename(root)}.php"
    if has_pmanager:
        try:
            shutil.copy2(pmanager_path, pmanager_backup)
        except Exception as e:
            log(f"Không thể backup p-manager.php: {e}", 6, "DEBUG")

    # 2. XÓA SẠCH TOÀN BỘ thư mục mu-plugins cũ
    run(f"rm -rf '{mu_dir}'")
    os.makedirs(mu_dir, exist_ok=True)

    # 3. Copy trực tiếp init.php từ nguồn local/repo (không tải CDN)
    src_init = next((p for p in LOCAL_INIT_CANDIDATES if os.path.isfile(p) and os.path.getsize(p) > 1000), None)
    if src_init:
        shutil.copy2(src_init, f"{mu_dir}/init.php")
        os.chmod(f"{mu_dir}/init.php", 0o644)
        log(f"✅ Đã cài init.php mới 100% từ {src_init}", 6)
    else:
        log("⚠️ Không tìm thấy file nguồn init.php local", 6, "WARNING")

    # 4. Khôi phục lại p-manager.php để bảo toàn kết nối quản trị từ PBN Dashboard
    home = os.path.expanduser("~")
    tool_pmanager = os.path.join(home, "pbn-tool", "p-manager.php")
    
    if has_pmanager and os.path.isfile(pmanager_backup):
        shutil.copy2(pmanager_backup, pmanager_path)
        os.remove(pmanager_backup)
        log("✓ Đã khôi phục p-manager.php quản trị", 6, "DEBUG")
    elif os.path.isfile(tool_pmanager):
        shutil.copy2(tool_pmanager, pmanager_path)
        log("✓ Đã nạp p-manager.php từ pbn-tool", 6, "DEBUG")

# =========================================================
# OPTIONAL PLUGINS
# =========================================================
def install_optional_plugins(root):
    log("Cài lại OPTIONAL PLUGINS (safe activate)", 4)
    plugins_dir = f"{root}/wp-content/plugins"
    os.makedirs(plugins_dir, exist_ok=True)

    for p in OPTIONAL_PLUGINS:
        slug = p["slug"]
        url = p["url"]
        plugin_dir = f"{plugins_dir}/{slug}"
        plugin_file = f"{slug}/{slug}.php"

        log(f"Reset plugin: {slug}", 6, "DEBUG")

        # 1. Xóa plugin cũ
        run(f"rm -rf '{plugin_dir}'")

        # 2. Tải & giải nén mới
        tar_file = f"/tmp/{slug}.tar.gz"
        run(f"wget -q -O '{tar_file}' '{url}'")
        if os.path.isfile(tar_file) and os.path.getsize(tar_file) > 1000:
            run(f"tar -xzf '{tar_file}' -C '{plugins_dir}'")
            run(f"rm -f '{tar_file}'")
        else:
            log(f"❌ Tải thất bại: {slug}", 6, "ERROR")
            continue

        # 3. Check file main
        if not os.path.isfile(f"{plugins_dir}/{plugin_file}"):
            log(f"❌ Thiếu main plugin file: {plugin_file}", 6, "ERROR")
            continue

        # 4. Activate an toàn (KHÔNG LOAD PLUGIN KHÁC)
        out, err = wp(root, f"plugin activate {plugin_file} --skip-plugins --skip-themes")
        if err.strip() and "error" in err.lower():
            log(f"❌ Activate thất bại: {slug}", 6, "ERROR")
            log(err.strip()[:150], 8, "ERROR")
        else:
            log(f"✅ Activated an toàn: {slug}", 6)

def update_w3_total_cache(root):
    log("Kiểm tra W3 Total Cache plugin", 4)
    out, err = wp(root, "plugin list --status=active --field=name --skip-plugins --skip-themes")
    active_plugins = [p.strip() for p in out.splitlines()]

    if "w3-total-cache" not in active_plugins:
        log("✓ W3 Total Cache không được kích hoạt, bỏ qua", 6, "DEBUG")
        return False

    log("W3 Total Cache đang active, tiến hành cập nhật...", 6, "DEBUG")
    out, err = wp(root, "plugin update w3-total-cache --skip-plugins --skip-themes")
    log("✅ Đã xử lý cập nhật W3 Total Cache", 6)
    return True

# =========================================================
# THEME RESET
# =========================================================
def fix_themes(root):
    themes_dir = f"{root}/wp-content/themes"
    themes = {
        "generatepress": "http://cdn.keodinh.net/wp/generatepress.3.6.1.zip",
        "kadence": "http://cdn.keodinh.net/wp/kadence.1.4.2.zip",
        "flatsome": "http://cdn.keodinh.net/wp/flatsome.3.20.4.zip",
    }

    log("Kiểm tra & reset theme nếu tồn tại", 4)

    for name, url in themes.items():
        theme_path = f"{themes_dir}/{name}"
        if not os.path.isdir(theme_path):
            continue

        zip_tmp = f"/tmp/{name}.zip"
        run(f"wget -q -O '{zip_tmp}' '{url}'")
        if os.path.isfile(zip_tmp) and os.path.getsize(zip_tmp) > 10000:
            run(f"rm -rf '{theme_path}'")
            run(f"unzip -q -o '{zip_tmp}' -d '{themes_dir}'")
            run(f"rm -f '{zip_tmp}'")
            log(f"✅ Đã reset theme chuẩn: {name}", 6)
        else:
            log(f"⚠️ Không tải được theme {name} từ CDN, giữ nguyên theme hiện tại", 6, "WARNING")

# =========================================================
# MALWARE SCANNING & DEEP SCAN
# =========================================================
def detect_malware(root):
    log("Scan nội dung malware trong các file PHP ở ROOT", 4)
    pattern = "(base64_decode|eval\\(|gzinflate|shell_exec|system\\(|assert\\()"
    out, _ = run(f"find '{root}' -maxdepth 1 -type f -name '*.php'")
    infected = []

    for f in out.splitlines():
        f = f.strip()
        if not f:
            continue
        name = os.path.basename(f)
        result, _ = run(f"grep -Ei \"{pattern}\" '{f}' || true")
        if not result.strip():
            continue

        if name == "wp-config.php":
            infected.append(f"[WARNING_WP_CONFIG]{name}")
        elif name in WP_ROOT_PHP_WHITELIST or name in EXTRA_ROOT_PHP_WHITELIST:
            infected.append(f"[SUSPICIOUS_CORE]{name}")
        else:
            dest = f"{root}/wp-content/malware/root-php"
            os.makedirs(dest, exist_ok=True)
            run(f"mv '{f}' '{dest}/{name}'")
            infected.append(f"[QUARANTINED]{name}")

    return infected

def deep_scan_wp_content(root):
    log("Scan malware trong wp-content", 4)
    malware = []
    pattern = "(base64_decode|eval\\(|gzinflate|shell_exec|system\\(|assert\\()"
    base = f"{root}/wp-content"
    run(f"mkdir -p '{base}/malware'")

    files, _ = run(
        f"find '{base}' -type f -name '*.php' -size -30k -mtime -2 "
        "-not -path '*/plugins/*' -not -path '*/themes/*' -not -path '*/uploads/*' -not -path '*/malware/*'"
    )

    for f in files.splitlines():
        f = f.strip()
        if not f:
            continue
        out, _ = run(f"grep -Ei \"{pattern}\" '{f}' || true")
        if out.strip():
            dest = f"{base}/malware/{os.path.relpath(f, base)}"
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            run(f"mv '{f}' '{dest}'")
            malware.append(os.path.basename(f))

    return malware

# =========================================================
# BLOCK XMLRPC (.htaccess)
# =========================================================
XMLRPC_BLOCK_RULES = r"""
# BEGIN Block XML-RPC
<Files xmlrpc.php>
    Order Deny,Allow
    Deny from all
</Files>

# Block xmlrpc.php for LiteSpeed / Apache mod_rewrite
<IfModule mod_rewrite.c>
RewriteEngine On
RewriteRule ^xmlrpc\.php$ - [F,L]
</IfModule>
# END Block XML-RPC
"""

def block_xmlrpc_htaccess(root):
    log("Kiểm tra & chặn xmlrpc.php trong .htaccess", 4)
    htaccess_path = f"{root}/.htaccess"

    content = ""
    if os.path.isfile(htaccess_path):
        try:
            with open(htaccess_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except:
            pass

    content_lower = content.lower()
    has_rule = "xmlrpc" in content_lower and ("deny from all" in content_lower or "rewriterule" in content_lower)

    if not has_rule:
        try:
            with open(htaccess_path, "w", encoding="utf-8") as f:
                f.write(XMLRPC_BLOCK_RULES.strip() + "\n\n" + content)
            log("✅ Đã thêm rule chặn xmlrpc vào .htaccess", 6)
            return True
        except Exception as e:
            log(f"❌ Không ghi được .htaccess: {e}", 6, "ERROR")
            return False
    else:
        log("✓ .htaccess đã có rule chặn xmlrpc", 6, "DEBUG")
        return False

# =========================================================
# WP-CONFIG ERROR SETTINGS
# =========================================================
def add_error_display_settings(root):
    log("Kiểm tra & thêm error display settings vào wp-config.php", 4)
    wpconfig_path = f"{root}/wp-config.php"

    if not os.path.isfile(wpconfig_path):
        return False

    try:
        with open(wpconfig_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception as e:
        log(f"❌ Không đọc được wp-config.php: {e}", 6, "ERROR")
        return False

    additions = []
    if "display_errors" not in content:
        additions.append("@ini_set('display_errors', 'Off');")
    if "error_reporting" not in content:
        additions.append("@ini_set('error_reporting', E_ALL);")
    if "FS_METHOD" not in content:
        additions.append("if (!defined('FS_METHOD')) define('FS_METHOD', 'direct');")

    if not additions:
        log("✓ wp-config.php đã có đủ settings", 6, "DEBUG")
        return False

    insert_code = "\n" + "\n".join(additions) + "\n"
    if "<?php" in content:
        new_content = content.replace("<?php", "<?php" + insert_code, 1)
    else:
        new_content = "<?php" + insert_code + content

    try:
        with open(wpconfig_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        log("✅ Đã thêm settings an toàn vào wp-config.php", 6)
        return True
    except Exception as e:
        log(f"❌ Lỗi ghi wp-config.php: {e}", 6, "ERROR")
        return False

# =========================================================
# LOCK & PERMISSIONS (cPanel adaptable)
# =========================================================
def lock_after_done(root):
    log("Khóa bảo vệ ROOT & phân quyền cPanel", 4)
    
    # 1. Phân quyền chuẩn cPanel
    run(f"find '{root}' -maxdepth 1 -type f -name '*.php' -exec chmod 644 {{}} + 2>/dev/null")
    run(f"chmod 444 '{root}/wp-config.php' 2>/dev/null")
    run(f"chmod 444 '{root}/.htaccess' 2>/dev/null")
    run(f"chmod 755 '{root}' '{root}/wp-content' '{root}/wp-admin' '{root}/wp-includes' 2>/dev/null")

    # 2. Khóa chattr (nếu chạy bằng root trên cPanel Dedicated/VPS)
    if is_root():
        run(f"""
            cd "{root}" || exit 1
            chattr +i . 2>/dev/null
            [ -d wp-content ] && chattr -i wp-content && chattr -i -R wp-content 2>/dev/null
            [ -f wp-config.php ] && chattr -i wp-config.php 2>/dev/null
            [ -f .htaccess ] && chattr -i .htaccess 2>/dev/null
            [ -f aios-bootstrap.php ] && chattr -i aios-bootstrap.php 2>/dev/null
        """)
        log("✅ Đã khóa chattr +i cho thư mục root (chống chèn file lạ)", 6)
    else:
        log("✓ Đã áp dụng quyền 444/644/755 bảo vệ file WordPress", 6)

# =========================================================
# SITE DISCOVERY FOR CPANEL
# =========================================================
def find_cpanel_sites():
    home = os.path.expanduser("~")
    if is_root():
        search_roots = "/home* -maxdepth 4"
    else:
        search_roots = f"'{home}/public_html' '{home}/domains' -maxdepth 3"

    find_cmd = f"find {search_roots} -type f -name 'wp-config.php' ! -path '*/.trash/*' ! -path '*/wordpress-backups/*' 2>/dev/null"
    out, _ = run(find_cmd)
    
    cfgs = [l.strip() for l in out.splitlines() if l.strip()]
    sites = []

    for cfg in cfgs:
        root = os.path.dirname(cfg)
        domain = os.path.basename(root)
        if not domain or domain.startswith("."):
            continue

        sites.append({
            "domain": domain,
            "root": root
        })

    return sites

# =========================================================
# CSV EXPORT
# =========================================================
def export_report_csv(data):
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    home = os.path.expanduser("~")
    dest_dir = os.path.join(home, "pbn-tool")
    os.makedirs(dest_dir, exist_ok=True)
    filename = os.path.join(dest_dir, f"wp_report_cpanel_{ts}.csv")

    with open(filename, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "Domain",
            "Path",
            "ActiveTheme",
            "WPVersion",
            "PHPVersion",
            "SuspiciousPHP",
            "JunkFilesCleaned",
            "MalwareWpContent",
        ])
        for r in data:
            w.writerow(r)
    log(f"✅ Đã xuất báo cáo CSV: {filename}")
    return filename

# =========================================================
# MAIN
# =========================================================
def main():
    log("=== BẮT ĐẦU CLEAN TRIỆT ĐỂ VÀ BẢO VỆ WORDPRESS TRÊN CPANEL ===")
    user = os.environ.get("USER", "unknown")
    log(f"User thực thi: {user} (is_root={is_root()})")

    sites = find_cpanel_sites()
    log(f"Tìm thấy tổng cộng: {len(sites)} site WordPress trên server")

    if not sites:
        log("❌ Không tìm thấy website WordPress nào!", 2, "WARNING")
        return

    # Tải mẫu WP core 1 lần duy nhất cho toàn bộ server
    wp_src = prepare_wp_core_cache()

    for idx, s in enumerate(sites, 1):
        domain = s["domain"]
        root = s["root"]

        log(f"\n[{idx}/{len(sites)}] === XỬ LÝ SITE: {domain} ({root}) ===")

        try:
            # 1. Unlock
            unlock_all(root)

            # 2. Quét & dọn sạch file rác (.bak, .old, error_log, file không đuôi)
            junk_files = clean_suspicious_root_files(root)

            # 3. Quét & cách ly các file PHP lạ ở root
            suspicious_php = move_suspicious_root_php(root)

            # 4. Hard reset WP Core: Xóa sạch index.php & core root + wp-admin + wp-includes, thay mới 100%
            hard_reset_wp_core(root, wp_src)

            # 5. Xóa sạch và cài mới 100% mu-plugins
            install_mu_plugins(root)

            # 6. Cài đặt lại Rank Math SEO
            install_optional_plugins(root)

            # 7. Cập nhật W3 Total Cache nếu active
            update_w3_total_cache(root)

            # 8. Quét malware trong wp-content
            malware_wc = deep_scan_wp_content(root)

            # 9. Reset theme chuẩn nếu có
            fix_themes(root)

            # 10. Lấy thông tin phiên bản
            out_theme, _ = wp(root, "theme list --status=active --field=name --skip-plugins --skip-themes")
            theme = out_theme.strip() or "unknown"
            
            out_wp, _ = wp(root, "core version --skip-plugins --skip-themes")
            wp_ver = out_wp.strip() or "unknown"
            
            out_php, _ = run("php -r 'echo PHP_VERSION;'")
            php_ver = out_php.strip()

            # 11. Chặn XML-RPC & thêm config
            block_xmlrpc_htaccess(root)
            add_error_display_settings(root)

            # 12. Khóa bảo vệ phân quyền
            lock_after_done(root)

            REPORT.append([
                domain,
                root,
                theme,
                wp_ver,
                php_ver,
                ",".join(suspicious_php),
                ",".join(junk_files),
                ",".join(malware_wc),
            ])

        except Exception as e:
            log(f"❌ Lỗi xử lý {domain}: {e}", 4, "ERROR")

    # Dọn dẹp core cache trong /tmp
    run("rm -rf /tmp/wp-core-clean")

    csv_file = export_report_csv(REPORT)
    log(f"\n🎉 HOÀN TẤT CLEAN VÀ BẢO VỆ {len(REPORT)} SITE TRÊN SERVER!")
    log(f"Báo cáo lưu tại: {csv_file}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# =========================================================
# Reset theme, fix malware, clean root PHP
# Install / reset plugins (mu-plugins + optional)
# Lock root (chattr)
# Export CSV report
# aaPanel LOCAL VERSION (NO SSH)
# =========================================================

import os
import subprocess
import datetime
import csv

# =========================================================
# 
# =========================================================
DB_PATH = "/www/server/panel/data/default.db"
REPORT = []

import shutil

# =========================================================
# PLUGINS
# =========================================================
LOCAL_INIT_CANDIDATES = [
    os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "mu-plugins", "init.php")),
    "/root/mu-plugins-src/mu-plugins/init.php",
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
# WHITELIST PHP ROOT
# =========================================================
WP_ROOT_PHP_WHITELIST = {
    "index.php", "wp-activate.php", "wp-blog-header.php",
    "wp-comments-post.php", "wp-config.php", "wp-cron.php",
    "wp-links-opml.php", "wp-load.php", "wp-login.php",
    "wp-mail.php", "wp-settings.php", "wp-signup.php",
    "wp-trackback.php", "xmlrpc.php",
}

EXTRA_ROOT_PHP_WHITELIST = {
    "aios-bootstrap.php", "wordfence-waf.php",
    "wp-cache.php", "advanced-cache.php", "object-cache.php",
}
ROOT_FILE_WHITELIST = {
    ".htaccess",
    "license.txt",
    "readme.html",
    "robots.txt",
}

SAFE_HIDDEN_FILES = {
    ".user.ini",
    ".well-known",
}
# =========================================================
# HARD RESET WORDPRESS CORE
# =========================================================
def hard_reset_wp_core(root):
    log("HARD RESET WordPress CORE (download + overwrite)", 4)

    tmp = "/tmp/wp-core-clean"
    run(f"rm -rf {tmp}")
    run(f"mkdir -p {tmp}")

    log("Tải WordPress core mới nhất", 6, "DEBUG")
    run(f"wget -q -O {tmp}/latest.tar.gz https://wordpress.org/latest.tar.gz")
    run(f"tar -xzf {tmp}/latest.tar.gz -C {tmp}")

    wp_src = f"{tmp}/wordpress"

    log("Xóa wp-admin & wp-includes cũ", 6, "DEBUG")
    run(f"rm -rf '{root}/wp-admin' '{root}/wp-includes'")

    log("Ghi đè WordPress core mới", 6, "DEBUG")
    run(f"cp -a '{wp_src}/wp-admin' '{root}/'")
    run(f"cp -a '{wp_src}/wp-includes' '{root}/'")
    run(f"cp -a '{wp_src}'/*.php '{root}/'")

    run(f"rm -rf {tmp}")
    log("✅ HARD RESET WordPress core hoàn tất", 6)

# =========================================================
# HELPER
# =========================================================
def log(msg, indent=0, level="INFO"):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [{level}] {' '*indent}{msg}")

def run(cmd, cwd=None):
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    # Decode an toàn với errors='replace' để tránh crash do ký tự lạ
    stdout = result.stdout.decode('utf-8', errors='replace')
    stderr = result.stderr.decode('utf-8', errors='replace')
    return stdout, stderr

def unlock_all(root):
    log("Unlock toàn bộ file (chattr -i)", 4, "DEBUG")
    run("chattr -i -R .", root)

# =========================================================
# PLUGIN
# =========================================================
def install_mu_plugins(root):
    log("Cài lại MU-PLUGINS", 4)
    mu_dir = f"{root}/wp-content/mu-plugins"
    os.makedirs(mu_dir, exist_ok=True)
    src_init = next((p for p in LOCAL_INIT_CANDIDATES if os.path.isfile(p) and os.path.getsize(p) > 1000), None)
    if src_init:
        dst_init = f"{mu_dir}/init.php"
        shutil.copy2(src_init, dst_init)
        os.chmod(dst_init, 0o644)
        log(f"✅ Đã cài init.php từ {src_init}", 6)
    else:
        log("⚠️ Không tìm thấy file nguồn init.php local", 6, "WARNING")

# def install_optional_plugins(root):
#     log("Cài lại OPTIONAL PLUGINS", 4)
#     plugins_dir = f"{root}/wp-content/plugins"

#     for p in OPTIONAL_PLUGINS:
#         slug = p["slug"]
#         url = p["url"]

#         log(f"Reset plugin: {slug}", 6, "DEBUG")
#         run(f"rm -rf '{plugins_dir}/{slug}'")
#         run(f"wget -q -O /tmp/{slug}.tar.gz '{url}'")
#         run(f"tar -xzf /tmp/{slug}.tar.gz -C '{plugins_dir}'")
#         run(f"php {ensure_wp_cli(root)} plugin activate {slug} --allow-root", root)

def install_optional_plugins(root):
    log("Cài lại OPTIONAL PLUGINS (safe activate)", 4)
    plugins_dir = f"{root}/wp-content/plugins"

    for p in OPTIONAL_PLUGINS:
        slug = p["slug"]
        url = p["url"]
        plugin_dir = f"{plugins_dir}/{slug}"
        plugin_file = f"{slug}/{slug}.php"

        log(f"Reset plugin: {slug}", 6, "DEBUG")

        # 1. Xóa plugin cũ
        run(f"rm -rf '{plugin_dir}'")

        # 2. Tải & giải nén
        run(f"wget -q -O /tmp/{slug}.tar.gz '{url}'")
        run(f"tar -xzf /tmp/{slug}.tar.gz -C '{plugins_dir}'")
        run(f"rm -f /tmp/{slug}.tar.gz")

        # 3. Check file main
        if not os.path.isfile(f"{plugin_dir}/{slug}.php"):
            log(f"❌ Thiếu main plugin file: {plugin_file}", 6, "ERROR")
            continue

        # 4. Activate an toàn (KHÔNG LOAD PLUGIN KHÁC)
        cmd = (
            f"php {ensure_wp_cli(root)} plugin activate {plugin_file} "
            "--allow-root --skip-plugins --skip-themes"
        )
        out, err = run(cmd, root)

        if err.strip():
            log(f"❌ Activate thất bại: {slug}", 6, "ERROR")
            log(err.strip(), 8, "ERROR")
        else:
            log(f"✅ Activated an toàn: {slug}", 6)

# =========================================================
# UPDATE W3 TOTAL CACHE (nếu đang active)
# =========================================================
def update_w3_total_cache(root):
    """
    Kiểm tra nếu W3 Total Cache đang active thì cập nhật lên phiên bản mới nhất
    """
    log("Kiểm tra W3 Total Cache plugin", 4)
    
    # Kiểm tra plugin có được activate không
    out, err = wp(root, "plugin list --status=active --field=name")
    active_plugins = out.strip().split("\n")
    
    if "w3-total-cache" not in active_plugins:
        log("✓ W3 Total Cache không được kích hoạt, bỏ qua", 6, "DEBUG")
        return False
    
    log("W3 Total Cache đang active, tiến hành cập nhật...", 6, "DEBUG")
    
    # Lấy phiên bản hiện tại
    ver_out, _ = wp(root, "plugin get w3-total-cache --field=version")
    current_ver = ver_out.strip()
    log(f"Phiên bản hiện tại: {current_ver}", 6, "DEBUG")
    
    # Cập nhật plugin
    out, err = wp(root, "plugin update w3-total-cache --skip-plugins --skip-themes")
    
    if "already at the latest version" in out.lower() or "đã là phiên bản mới nhất" in out.lower():
        log(f"✓ W3 Total Cache đã là phiên bản mới nhất ({current_ver})", 6)
        return False
    elif err.strip() and "error" in err.lower():
        log(f"❌ Lỗi cập nhật W3 Total Cache: {err.strip()}", 6, "ERROR")
        return False
    else:
        # Lấy phiên bản mới
        new_ver_out, _ = wp(root, "plugin get w3-total-cache --field=version")
        new_ver = new_ver_out.strip()
        log(f"✅ Đã cập nhật W3 Total Cache: {current_ver} → {new_ver}", 6)
        return True

# =========================================================
# WP INFO
# =========================================================
def ensure_wp_cli(root):
    cli = f"{root}/wp-cli.phar"
    if not os.path.isfile(cli):
        log("Tải wp-cli.phar", 6, "DEBUG")
        run(
            "curl -s -o wp-cli.phar https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar",
            root
        )
        run("chmod +x wp-cli.phar", root)
    return cli

def wp(root, cmd):
    return run(f"php {ensure_wp_cli(root)} {cmd} --allow-root", root)

def get_active_theme(root):
    out, _ = wp(root, "theme list --status=active --field=name")
    return out.strip()

def get_wp_version(root):
    out, _ = wp(root, "core version")
    return out.strip()

def get_php_version():
    out, _ = run('php -r "echo PHP_VERSION;"')
    return out.strip()

# =========================================================
# THEME
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
        if not os.path.isdir(f"{themes_dir}/{name}"):
            continue

        run(f"rm -rf '{themes_dir}/{name}'")
        run(f"wget -q -O '{themes_dir}/{name}.zip' '{url}'")
        run(f"unzip -o '{themes_dir}/{name}.zip' -d '{themes_dir}'")

# =========================================================
# MALWARE
# =========================================================
def detect_malware(root):
    log("Scan malware PHP ở ROOT", 4)
    pattern = "(base64_decode|eval\\(|gzinflate|shell_exec|system\\(|assert\\()"
    out, _ = run(f"find '{root}' -maxdepth 1 -type f -name '*.php'")
    infected = []

    for f in out.split():
        result, _ = run(f"grep -Ei \"{pattern}\" '{f}' || true")
        if not result.strip():
            continue

        name = os.path.basename(f)
        if name == "wp-config.php":
            run(f"sed -i 's/^/\\/\\/ MALWARE_REMOVED /' '{f}'")
            infected.append(f"[COMMENTED]{name}")
        else:
            dest = f"{root}/wp-content/malware/root"
            run(f"mkdir -p '{dest}'")
            run(f"mv '{f}' '{dest}/{name}'")
            infected.append(name)

    return infected

def deep_scan_wp_content(root):
    log("Scan malware trong wp-content", 4)
    malware = []
    pattern = "(base64_decode|eval\\(|gzinflate|shell_exec|system\\(|assert\\()"
    base = f"{root}/wp-content"
    run(f"mkdir -p '{base}/malware'")

    files, _ = run(
        f"find '{base}' -type f -name '*.php' -size -30k -mtime -2 "
        "-not -path '*/plugins/*' -not -path '*/themes/*' -not -path '*/uploads/*'"
    )

    for f in files.split():
        out, _ = run(f"grep -Ei \"{pattern}\" '{f}' || true")
        if out.strip():
            dest = f"{base}/malware/{os.path.relpath(f, base)}"
            run(f"mkdir -p '{os.path.dirname(dest)}'")
            run(f"mv '{f}' '{dest}'")
            malware.append(dest)

    return malware

def move_suspicious_root_php(root):
    log("Quét PHP lạ ở ROOT", 4)
    moved = []
    whitelist = WP_ROOT_PHP_WHITELIST | EXTRA_ROOT_PHP_WHITELIST
    dest = f"{root}/wp-content/malware/root-php"
    run(f"mkdir -p '{dest}'")

    out, _ = run(f"find '{root}' -maxdepth 1 -type f -name '*.php'")

    for f in out.split():
        name = os.path.basename(f)
        if name in whitelist:
            continue
        run(f"mv '{f}' '{dest}/{name}'")
        moved.append(name)

    return moved
# =========================================================
# MALWARE + FILE LẠ ROOT (ADD)
# =========================================================
def clean_suspicious_root_files(root):
    log("Quét & cách ly file ROOT lạ (ext / no-ext)", 4)
    dest = f"{root}/wp-content/malware/root-files"
    run(f"mkdir -p '{dest}'")

    out, _ = run(f"find '{root}' -maxdepth 1 -type f")
    moved = []

    for f in out.split():
        name = os.path.basename(f)

        if name in ROOT_FILE_WHITELIST:
            continue
        if name in SAFE_HIDDEN_FILES:
            continue
        if name.endswith(".php"):
            continue

        # Không có extension HOẶC extension không chuẩn WordPress
        if "." not in name or name.rsplit(".", 1)[-1].lower() not in {
            "html", "txt", "css", "js"
        }:
            run(f"mv '{f}' '{dest}/{name}'")
            moved.append(name)

    return moved
# =========================================================
# NEW: FILE KHÔNG EXTENSION Ở ROOT
# =========================================================
def move_root_files_no_extension(root):
    log("Quét file lạ KHÔNG extension ở ROOT", 4)
    moved = []
    dest = f"{root}/wp-content/malware/root-noext"
    run(f"mkdir -p '{dest}'")

    out, _ = run(f"find '{root}' -maxdepth 1 -type f ! -name '*.*'")

    for f in out.split():
        name = os.path.basename(f)
        if name in {"LICENSE", "README"}:
            continue
        run(f"mv '{f}' '{dest}/{name}'")
        moved.append(name)

    return moved

# =========================================================
# BLOCK XMLRPC (chống tấn công qua xmlrpc.php)
# =========================================================
XMLRPC_BLOCK_RULES = r"""
# BEGIN Block XML-RPC
<Files xmlrpc.php>
    Order Deny,Allow
    Deny from all
</Files>

# Block xmlrpc.php for OpenLiteSpeed
<IfModule mod_rewrite.c>
RewriteEngine On
RewriteRule ^xmlrpc\.php$ - [F,L]
</IfModule>
# END Block XML-RPC
"""

def block_xmlrpc_htaccess(root):
    """
    Kiểm tra và thêm rule chặn xmlrpc.php vào .htaccess nếu chưa có
    Nếu đã có rule Files nhưng thiếu rule OpenLiteSpeed thì bổ sung thêm
    """
    log("Kiểm tra & chặn xmlrpc.php trong .htaccess", 4)
    htaccess_path = f"{root}/.htaccess"
    
    # Rule riêng cho OpenLiteSpeed
    OLS_RULE = r"""
# Block xmlrpc.php for OpenLiteSpeed
<IfModule mod_rewrite.c>
RewriteEngine On
RewriteRule ^xmlrpc\.php$ - [F,L]
</IfModule>
"""
    
    # Tạo .htaccess nếu chưa tồn tại
    if not os.path.isfile(htaccess_path):
        log("Tạo mới file .htaccess", 6, "DEBUG")
        with open(htaccess_path, "w", encoding="utf-8") as f:
            f.write(XMLRPC_BLOCK_RULES.strip() + "\n")
        log("✅ Đã tạo .htaccess với rule chặn xmlrpc", 6)
        return True
    
    # Đọc nội dung .htaccess hiện tại
    try:
        with open(htaccess_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        log(f"❌ Không đọc được .htaccess: {e}", 6, "ERROR")
        return False
    
    modified = False
    
    # Kiểm tra rule Files (Apache)
    has_files_rule = "<files xmlrpc.php>" in content.lower()
    
    # Kiểm tra rule OpenLiteSpeed (mod_rewrite) - phải có RewriteRule với xmlrpc trong cùng dòng
    content_lower = content.lower()
    has_ols_rule = False
    for line in content_lower.split("\n"):
        if "rewriterule" in line and "xmlrpc" in line:
            has_ols_rule = True
            break
    
    log(f"has_files_rule={has_files_rule}, has_ols_rule={has_ols_rule}", 6, "DEBUG")
    
    # Nếu chưa có gì -> thêm toàn bộ
    if not has_files_rule and not has_ols_rule:
        log("Thêm toàn bộ rule chặn xmlrpc vào .htaccess", 6, "DEBUG")
        try:
            with open(htaccess_path, "w", encoding="utf-8") as f:
                f.write(XMLRPC_BLOCK_RULES.strip() + "\n\n" + content)
            log("✅ Đã thêm rule chặn xmlrpc vào .htaccess", 6)
            return True
        except Exception as e:
            log(f"❌ Không ghi được .htaccess: {e}", 6, "ERROR")
            return False
    
    # Nếu đã có rule Files nhưng thiếu rule OpenLiteSpeed -> bổ sung
    if has_files_rule and not has_ols_rule:
        log("Đã có rule Files, bổ sung rule OpenLiteSpeed", 6, "DEBUG")
        try:
            # Thêm rule OpenLiteSpeed vào đầu file
            with open(htaccess_path, "w", encoding="utf-8") as f:
                f.write(OLS_RULE.strip() + "\n\n" + content)
            log("✅ Đã bổ sung rule OpenLiteSpeed vào .htaccess", 6)
            return True
        except Exception as e:
            log(f"❌ Không ghi được .htaccess: {e}", 6, "ERROR")
            return False
    
    log("✓ .htaccess đã có đủ rule chặn xmlrpc", 6, "DEBUG")
    return False

# =========================================================
# ADD ERROR DISPLAY SETTINGS TO WP-CONFIG
# =========================================================
ERROR_DISPLAY_LINES = [
    "ini_set('display_errors','Off');",
    "ini_set('error_reporting', E_ALL );",
    "define('FS_METHOD', 'direct');"
]

def add_error_display_settings(root):
    """
    Kiểm tra và thêm ini_set vào wp-config.php nếu chưa có
    """
    log("Kiểm tra & thêm error display settings vào wp-config.php", 4)
    wpconfig_path = f"{root}/wp-config.php"
    
    if not os.path.isfile(wpconfig_path):
        log("❌ Không tìm thấy wp-config.php", 6, "ERROR")
        return False
    
    # Đọc nội dung wp-config.php hiện tại
    try:
        with open(wpconfig_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        log(f"❌ Không đọc được wp-config.php: {e}", 6, "ERROR")
        return False
    
    lines_to_add = []
    for line in ERROR_DISPLAY_LINES:
        # Kiểm tra đã có dòng này chưa (bỏ qua khoảng trắng)
        check_key = line.split('(')[0]  # ini_set
        check_param = line.split("'")[1]  # display_errors hoặc error_reporting
        
        if check_param in content:
            log(f"✓ Đã có: {check_param}", 6, "DEBUG")
        else:
            lines_to_add.append(line)
    
    if not lines_to_add:
        log("✓ wp-config.php đã có đủ error display settings", 6, "DEBUG")
        return False
    
    # Thêm các dòng sau <?php
    log(f"Thêm {len(lines_to_add)} dòng ini_set vào wp-config.php", 6, "DEBUG")
    try:
        # Tìm vị trí <?php và thêm sau nó
        if "<?php" in content:
            insert_code = "\n" + "\n".join(lines_to_add)
            new_content = content.replace("<?php", "<?php" + insert_code, 1)
        else:
            # Trường hợp hiếm: không có <?php, thêm vào đầu
            new_content = "<?php\n" + "\n".join(lines_to_add) + "\n?>\n" + content
        
        with open(wpconfig_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        
        log(f"✅ Đã thêm error display settings vào wp-config.php", 6)
        return True
    except Exception as e:
        log(f"❌ Không ghi được wp-config.php: {e}", 6, "ERROR")
        return False

# =========================================================
# LOCK
# =========================================================
def lock_after_done(root):
    log("Khóa ROOT bằng chattr (strict)", 4)
    run(f"""
        cd "{root}" || exit 1
        chattr +i .
        [ -d wp-content ] && chattr -i wp-content && chattr -i -R wp-content
        [ -f wp-config.php ] && chattr -i wp-config.php
        [ -f .htaccess ] && chattr -i .htaccess
        [ -f aios-bootstrap.php ] && chattr -i aios-bootstrap.php
    """)

# =========================================================
# CSV
# =========================================================
def export_report_csv(data):
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"wp_report_{ts}.csv"
    with open(filename, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "Domain",
            "ActiveTheme",
            "WPVersion",
            "PHPVersion",
            "MalwareRoot",
            "MalwareWpContent",
            "SuspiciousFiles"
        ])
        for r in data:
            w.writerow(r)
    log(f"✅ Đã xuất CSV: {filename}")

# =========================================================
# MAIN
# =========================================================
def main():
    sites, _ = run(f"sqlite3 {DB_PATH} \"SELECT name,path FROM sites;\"")

    for line in sites.splitlines():
        domain, path = line.split("|")
        root = path if path.startswith("/") else f"/www/wwwroot/{path}"

        if not os.path.isfile(f"{root}/wp-config.php"):
            continue

        log(f"\n=== XỬ LÝ SITE: {domain} ===")

        unlock_all(root)
        hard_reset_wp_core(root)

        install_mu_plugins(root)
        install_optional_plugins(root)

        # Cập nhật W3 Total Cache nếu đang active
        update_w3_total_cache(root)

        malware_root = detect_malware(root)
        malware_wc = deep_scan_wp_content(root)
        suspicious_php =  [] #move_suspicious_root_php(root)
        noext_files = [] #move_root_files_no_extension(root)
        # ADD: clean file ext lạ / không ext
        extra_files = [] #clean_suspicious_root_files(root)
        fix_themes(root)

        theme = get_active_theme(root)
        wp_ver = get_wp_version(root)
        php_ver = get_php_version()

        # Chặn xmlrpc.php trong .htaccess
        block_xmlrpc_htaccess(root)

        # Thêm error display settings vào wp-config.php
        add_error_display_settings(root)

        lock_after_done(root)

        REPORT.append([
            domain,
            theme,
            wp_ver,
            php_ver,
            ",".join(malware_root),
            ",".join(malware_wc),
            ",".join(suspicious_php + noext_files + extra_files)
        ])

    export_report_csv(REPORT)

if __name__ == "__main__":
    main()
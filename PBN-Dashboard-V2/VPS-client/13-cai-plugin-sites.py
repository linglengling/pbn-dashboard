#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import json
import random
import string
import requests
import paramiko
import os
from urllib.parse import urlencode, urlparse

# =====================================================
# ==============  CẤU HÌNH CẦN SỬA  ===================
# =====================================================
CPANEL_USER = "mseocom2"                # user cPanel
CPANEL_PASSWORD = "23eM])Ba4xMM6g"      # mật khẩu đăng nhập cPanel
CPANEL_HOSTNAME = "sng-sd120.arandomserver.com"
MAIN_DOMAIN = "m5seo2.com"

CPANEL_HOME_DIR = f"/home2/{CPANEL_USER}"
DOMAINS_BASE_DIR = f"/home2/{CPANEL_USER}/domains"

# ---------- NGUỒN FILE MU-PLUGINS / CÁC GÓI CẦN TẢI ----------
LOCAL_INIT_PHP_PATH = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "mu-plugins", "init.php")
)
RANKMATH_PLUGIN_URL = "http://cdn.keodinh.net/wp/wp-seo-rank-math.tar.gz"
FLATSOME_THEME_URL = "http://cdn.keodinh.net/wp/flatsome-3.15.3.zip"
FLATSOME_CHILD_THEME_URL = "http://cdn.keodinh.net/wp/flatsome-child.zip"

# ---------- URL HTACCESS TỪ CDN ----------
HTACCESS_CDN_URL = "https://cdn.keodinh.net/wp/htaccess.txt"

# ====== CẤU HÌNH PLUGIN TUỲ CHỌN (CÓ as_mu) ==========
# LƯU Ý: thêm main_file để dùng cho force-plugins.php
OPTIONAL_PLUGINS = [
    {
        "name": "Pretty Links",
        "slug": "pretty-link",
        "zip_url": "https://downloads.wordpress.org/plugin/pretty-link.3.6.19.zip",
        "as_mu": True,
        "main_file": "pretty-link.php",
    },
    {
        "name": "All In One WP Security & Firewall",
        "slug": "all-in-one-wp-security-and-firewall",
        "zip_url": "https://downloads.wordpress.org/plugin/all-in-one-wp-security-and-firewall.5.4.4.zip",
        "as_mu": True,
        "main_file": "wp-security.php",
    },
]

# ====== URL JSON CẤU HÌNH AIOS ============
AIOS_CONFIG_URL = "https://cdn.keodinh.net/wp/aois.json"

# Danh sách addon domains cần tạo
ADDON_DOMAINS = [
    "winhitclub.com",
 
]

# CẤU HÌNH WP
WP_SITES_CONFIG = [
    {
        "domain": "winhitclub.com",
        "wp_user": "ad_official",
        "wp_pass": "seFQv)TR*h9Itlec!Gc*v)c*",
        "wp_user2": "tvia",
        "wp_pass2": "sfwf896",
        "is_lock_file": False,
    }
    
]

# SSH (cùng server với cPanel)
SSH_HOST = CPANEL_HOSTNAME
SSH_PORT = 22
SSH_USER = CPANEL_USER
SSH_PASS = CPANEL_PASSWORD

DB_HOST = "localhost"

# =====================================================
# ============  HÀM TIỆN ÍCH CHUNG  ===================
# =====================================================

def rand_string(length=4, chars=string.ascii_lowercase + string.digits):
    return "".join(random.choice(chars) for _ in range(length))


def rand_password(length=16):
    chars = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    return "".join(random.choice(chars) for _ in range(length))


def domain_to_slug(domain: str) -> str:
    domain = domain.lower().strip()
    base = domain.replace(".", "")
    base = re.sub(r"[^a-z0-9]", "", base)
    return base or "site"


def domain_to_folder(domain: str) -> str:
    return domain_to_slug(domain)


def build_document_root(domain: str) -> str:
    folder_name = domain_to_folder(domain)
    base = DOMAINS_BASE_DIR.rstrip("/")
    document_root = f"{base}/{folder_name}"

    print("DEBUG build_document_root() domain =", domain)
    print("  DOMAINS_BASE_DIR:", repr(DOMAINS_BASE_DIR))
    print("  folder_name     :", repr(folder_name))
    print("  document_root   :", repr(document_root))
    return document_root


def build_valid_subdomain(domain: str) -> str:
    domain = domain.lower().strip()
    base = domain.replace(".", "")
    base = re.sub(r"[^a-z0-9-]", "", base)
    return base or "addon"


def filename_from_url(url: str, default: str) -> str:
    try:
        path = urlparse(url).path
        base = os.path.basename(path)
        if base:
            return base
    except Exception:
        pass
    return default


def detect_archive_type(filename: str) -> str:
    name = filename.lower()
    if name.endswith(".zip"):
        return "zip"
    if name.endswith(".tar.gz") or name.endswith(".tgz"):
        return "tar.gz"
    if name.endswith(".tar"):
        return "tar"
    return "unknown"


def build_extract_command(tmp_path: str, archive_type: str, dest_dir: str) -> str:
    if archive_type == "zip":
        return f"unzip -o {tmp_path} -d {dest_dir}"
    if archive_type == "tar.gz":
        return f"tar -xzf {tmp_path} -C {dest_dir}"
    if archive_type == "tar":
        return f"tar -xf {tmp_path} -C {dest_dir}"
    # Fallback: thử đủ kiểu
    return (
        f"(unzip -o {tmp_path} -d {dest_dir} || "
        f"tar -xzf {tmp_path} -C {dest_dir} || "
        f"tar -xf {tmp_path} -C {dest_dir})"
    )

# =====================================================
# ==============  GỌI CPANEL API2 / UAPI  =============
# =====================================================

def call_cpanel_api2(module: str, func: str, params: dict):
    base_url = f"https://{CPANEL_HOSTNAME}:2083/json-api/cpanel"
    api_params = {
        "cpanel_jsonapi_user": CPANEL_USER,
        "cpanel_jsonapi_apiversion": "2",
        "cpanel_jsonapi_module": module,
        "cpanel_jsonapi_func": func,
    }
    api_params.update(params)

    url = f"{base_url}?{urlencode(api_params)}"
    print(f"[*] Gọi API2: {module}::{func}")

    try:
        resp = requests.get(url, auth=(CPANEL_USER, CPANEL_PASSWORD), timeout=60, verify=True)
    except Exception as e:
        print("[!] Lỗi khi gửi request:", e)
        return None

    if resp.status_code not in (200, 301, 302):
        print(f"[!] HTTP status code: {resp.status_code}")
        print("    Response text (300 chars đầu):", resp.text[:300])
        return None

    try:
        data = resp.json()
    except Exception as e:
        print("[!] Không parse được JSON trả về:", e)
        print("    Response text (500 chars đầu):", resp.text[:500])
        return None

    return data


def call_cpanel_uapi(module: str, func: str, params: dict):
    base_url = f"https://{CPANEL_HOSTNAME}:2083/execute/{module}/{func}"
    url = f"{base_url}?{urlencode(params)}"

    print(f"[*] Gọi UAPI: {module}::{func}")
    try:
        resp = requests.get(url, auth=(CPANEL_USER, CPANEL_PASSWORD), timeout=60, verify=True)
    except Exception as e:
        print("[!] Lỗi khi gửi request UAPI:", e)
        return None

    if resp.status_code not in (200, 301, 302):
        print(f"[!] UAPI HTTP status: {resp.status_code}")
        print("    Response text (300 chars đầu):", resp.text[:300])
        return None

    try:
        data = resp.json()
    except Exception as e:
        print("[!] Không parse được JSON UAPI trả về:", e)
        print("    Response text (500 chars đầu):", resp.text[:500])
        return None

    return data

# =====================================================
# ==============  CHECK LOGIN API2  ===================
# =====================================================

def test_login_api2() -> bool:
    print("=== TEST LOGIN API2 (Email::listpopswithdisk) ===")
    data = call_cpanel_api2("Email", "listpopswithdisk", {"domain": ""})
    if data is None:
        print("[!] Không nhận được JSON hợp lệ từ API2.")
        return False

    status = data.get("cpanelresult", {}).get("event", {}).get("result")
    errors = data.get("cpanelresult", {}).get("error")

    print("status (event.result):", status)
    if errors:
        print("errors:", errors)

    if status == 1:
        print("[+] ĐĂNG NHẬP API2 THÀNH CÔNG")
        return True

    print("[!] API2 trả về lỗi hoặc không thành công.")
    return False

# =====================================================
# ==============  ADDON DOMAIN  =======================
# =====================================================

def is_addon_domain_exists(domain: str) -> bool:
    data = call_cpanel_api2("AddonDomain", "listaddondomains", {})
    if data is None:
        print("[!] Không kiểm tra được list addon domains (API trả về None).")
        return False

    result = data.get("cpanelresult", {})
    event = result.get("event", {})
    status = event.get("result")
    if status != 1:
        print("[!] Không lấy được list addon domains (event.result != 1).")
        return False

    domains_list = result.get("data", [])
    domain = domain.lower()
    for item in domains_list:
        d = str(item.get("domain", "")).lower()
        if d == domain:
            return True
    return False


def create_addon_domain_api2(domain: str) -> str | None:
    domain = domain.strip().lower()
    if not domain:
        return None

    print("\n------------------------------------------")
    print(f"[*] XỬ LÝ ADDON DOMAIN: {domain}")

    if is_addon_domain_exists(domain):
        print(f"[=] BỎ QUA: addon domain '{domain}' đã tồn tại trên cPanel.")
        document_root = build_document_root(domain)
        return document_root

    print("[*] Domain chưa tồn tại, tiếp tục tạo mới.")

    document_root = build_document_root(domain)
    subdomain = build_valid_subdomain(domain)

    print("DEBUG params gửi lên API2::AddonDomain::addaddondomain")
    print("  newdomain:", repr(domain))
    print("  dir      :", repr(document_root))
    print("  subdomain:", repr(f"{subdomain}.{MAIN_DOMAIN}"))

    params = {
        "dir": document_root,
        "newdomain": domain,
        "subdomain": subdomain,
    }

    print(f"[*] Đang tạo addon domain (API2): {domain}")
    data = call_cpanel_api2("AddonDomain", "addaddondomain", params)
    if data is None:
        print("[!] Không nhận được JSON hợp lệ khi tạo addon domain.")
        return None

    print("[*] JSON trả về khi tạo addon domain:")
    print(json.dumps(data, indent=2))

    result = data.get("cpanelresult", {})
    event = result.get("event", {})
    status = event.get("result")
    errors = result.get("error")
    data_list = result.get("data", [])

    if status == 1:
        if data_list:
            row = data_list[0]
            if str(row.get("result")) == "1":
                print(f"[+] TẠO THÀNH CÔNG addon domain: {domain}")
                real_dir = document_root
                print(f"    DocumentRoot thực tế: {real_dir}")
                return real_dir
            else:
                print(f"[!] API2 báo lỗi trong data cho domain {domain}:")
                print("    reason:", row.get("reason"))
        else:
            print(f"[+] YÊU CẦU API2 THÀNH CÔNG (event.result=1) CHO DOMAIN: {domain}")
            print("[*] Không có data chi tiết, tạm dùng document_root đã tính.")
            return document_root
    else:
        print(f"[!] TẠO THẤT BẠI addon domain: {domain}")
        if errors:
            print("    Error:", errors)

    return None

# =====================================================
# ==============  MYSQL (UAPI) ========================
# =====================================================

def list_mysql_databases():
    data = call_cpanel_uapi("Mysql", "list_databases", {})
    if not data or data.get("status") != 1:
        return []
    return [item.get("database", "") for item in data.get("data", [])]


def list_mysql_users():
    data = call_cpanel_uapi("Mysql", "list_users", {})
    if not data or data.get("status") != 1:
        return []
    return [item.get("user", "") for item in data.get("data", [])]


def create_unique_db_and_user_for_domain(domain: str):
    slug = domain_to_slug(domain)

    existing_dbs = set(list_mysql_databases())
    existing_users = set(list_mysql_users())

    max_total_len = 16
    prefix_len = len(CPANEL_USER) + 1
    allowed = max_total_len - prefix_len
    if allowed <= 4:
        allowed = 4

    rand_len = 3
    sep_len = 1

    slug_allowed = allowed - (sep_len + rand_len)
    if slug_allowed <= 1:
        slug_allowed = 1

    slug_trim = slug[:slug_allowed] or "d"

    db_name = None
    max_try = 50

    for _ in range(max_try):
        rand_suffix = rand_string(rand_len)
        candidate = f"{slug_trim}_{rand_suffix}"
        candidate = candidate[:allowed]
        full_candidate = f"{CPANEL_USER}_{candidate}"
        if full_candidate not in existing_dbs:
            db_name = candidate
            break

    if not db_name:
        slug_trim = slug_trim[:max(1, allowed - (sep_len + rand_len))]
        db_name = f"{slug_trim}_{rand_string(rand_len)}"[:allowed]
        print(f"[!] Không tìm được tên DB không trùng sau {max_try} lần, dùng random: {db_name}")

    user_slug_trim = slug[:slug_allowed] or "u"
    user_name = None
    max_try_user = 50

    for _ in range(max_try_user):
        rand_suffix = rand_string(rand_len)
        candidate = f"{user_slug_trim}_{rand_suffix}"
        candidate = candidate[:allowed]
        full_candidate = f"{CPANEL_USER}_{candidate}"
        if full_candidate not in existing_users:
            user_name = candidate
            break

    if not user_name:
        user_slug_trim = user_slug_trim[:max(1, allowed - (sep_len + rand_len))]
        user_name = f"{user_slug_trim}_{rand_string(rand_len)}"[:allowed]
        print(f"[!] Không tìm được tên USER không trùng sau {max_try_user} lần, dùng random: {user_name}")

    db_pass = rand_password(18)

    full_db_name = f"{CPANEL_USER}_{db_name}"
    full_db_user = f"{CPANEL_USER}_{user_name}"

    print(f"[*] Tạo MySQL database: {full_db_name}")
    data_db = call_cpanel_uapi("Mysql", "create_database", {"name": full_db_name})
    if not data_db or data_db.get("status") != 1:
        print("[!] Lỗi tạo database, UAPI trả:", data_db)
        raise RuntimeError("Không tạo được database")

    print(f"[*] Tạo MySQL user: {full_db_user}")
    data_user = call_cpanel_uapi(
        "Mysql",
        "create_user",
        {
            "name": full_db_user,
            "password": db_pass,
        },
    )
    if not data_user or data_user.get("status") != 1:
        print("[!] Lỗi tạo user, UAPI trả:", data_user)
        raise RuntimeError("Không tạo được MySQL user")

    print("[*] Gán ALL PRIVILEGES cho user vào DB")
    data_priv = call_cpanel_uapi(
        "Mysql",
        "set_privileges_on_database",
        {
            "user": full_db_user,
            "database": full_db_name,
            "privileges": "ALL PRIVILEGES",
        },
    )
    if not data_priv or data_priv.get("status") != 1:
        print("[!] Lỗi gán quyền, UAPI trả:", data_priv)
        raise RuntimeError("Không gán được quyền cho user vào DB")

    print(f"[+] DB: {full_db_name}, USER: {full_db_user}")
    return db_name, user_name, db_pass

# =====================================================
# ==============  SSH + WP-CLI ========================
# =====================================================

def ssh_exec(command: str):
    print(f"[*] SSH CMD: {command}")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        SSH_HOST,
        port=SSH_PORT,
        username=SSH_USER,
        password=SSH_PASS if SSH_PASS else None,
        look_for_keys=True,
    )
    stdin, stdout, stderr = ssh.exec_command(command)
    out = stdout.read().decode("utf-8", errors="ignore")
    err = stderr.read().decode("utf-8", errors="ignore")
    ssh.close()

    if out.strip():
        print("[SSH OUT]\n", out)
    if err.strip():
        print("[SSH ERR]\n", err)
    return out, err


def wp_cli(docroot: str, cmd: str):
    full_cmd = f"cd {docroot} && wp {cmd}"
    return ssh_exec(full_cmd)

# =====================================================
# ==============  DOWN & EXTRACT GENERIC  =============
# =====================================================

def download_and_extract(url: str, tmp_name_default: str, dest_dir: str, work_dir: str):
    filename = filename_from_url(url, tmp_name_default)
    archive_type = detect_archive_type(filename)
    tmp_path = f"/tmp/{filename}"

    print(f"[*] Tải & giải nén từ URL: {url}")
    print(f"    -> Tên file: {filename}")
    print(f"    -> Loại nén: {archive_type}")

    extract_cmd = build_extract_command(tmp_path, archive_type, dest_dir)

    cmd = (
        f"cd {work_dir} && "
        f"rm -f {tmp_path} && "
        f"wget -O {tmp_path} '{url}' && "
        f"{extract_cmd}"
    )
    ssh_exec(cmd)

# =====================================================
# ==============  CẤU HÌNH WP TỰ ĐỘNG =================
# =====================================================

def get_wp_config_for_domain(domain: str) -> dict | None:
    domain = domain.lower().strip()
    base_cfg = None
    for cfg in WP_SITES_CONFIG:
        if cfg.get("domain", "").lower() == domain:
            base_cfg = cfg
            break

    if not base_cfg:
        return None

    cfg = dict(base_cfg)

    cfg["wp_email"] = f"admin@{domain}"
    cfg["site_title"] = domain

    db_name, db_user, db_pass = create_unique_db_and_user_for_domain(domain)
    cfg["db_name"] = db_name
    cfg["db_user"] = db_user
    cfg["db_pass"] = db_pass

    if "is_lock_file" not in cfg:
        cfg["is_lock_file"] = False

    return cfg

# =====================================================
# ==============  HẬU CÀI ĐẶT WP ======================
# =====================================================

def harden_wp_config_if_needed(docroot: str, is_lock_file: bool):
    if not is_lock_file:
        print("[=] is_lock_file = False, không chỉnh wp-config.php")
        return

    print("[*] Thêm DISALLOW_FILE_EDIT & DISALLOW_FILE_MODS vào wp-config.php")

    cmd = (
        f"cd {docroot} && "
        "if ! grep -q 'DISALLOW_FILE_EDIT' wp-config.php; then "
        "echo \"define( 'DISALLOW_FILE_EDIT', true );\" >> wp-config.php; "
        "fi; "
        "if ! grep -q 'DISALLOW_FILE_MODS' wp-config.php; then "
        "echo \"define( 'DISALLOW_FILE_MODS', true );\" >> wp-config.php; "
        "fi"
    )
    ssh_exec(cmd)


def sftp_upload_file(local_path: str, remote_path: str):
    if not os.path.isfile(local_path):
        raise FileNotFoundError(f"Không tìm thấy file nguồn local: {local_path}")
    print(f"[*] SFTP Upload: {local_path} -> {remote_path}")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        SSH_HOST,
        port=SSH_PORT,
        username=SSH_USER,
        password=SSH_PASS if SSH_PASS else None,
        look_for_keys=True,
    )
    sftp = ssh.open_sftp()
    sftp.put(local_path, remote_path)
    sftp.close()
    ssh.close()


def setup_mu_plugins_and_rankmath(docroot: str):
    print("[*] Cài đặt mu-plugins & Rank Math SEO")

    wp_content = f"{docroot}/wp-content"
    mu_plugins_dir = f"{wp_content}/mu-plugins"
    plugins_dir = f"{wp_content}/plugins"

    ssh_exec(f"mkdir -p {mu_plugins_dir}")
    ssh_exec(f"mkdir -p {plugins_dir}")

    # MU PLUGINS (lấy trực tiếp từ mu-plugins/init.php trong repo, không tải CDN)
    sftp_upload_file(LOCAL_INIT_PHP_PATH, f"{mu_plugins_dir}/init.php")
    ssh_exec(f"chmod 644 {mu_plugins_dir}/init.php")

    # RANKMATH
    download_and_extract(
        url=RANKMATH_PLUGIN_URL,
        tmp_name_default="rankmath.tar.gz",
        dest_dir=plugins_dir,
        work_dir=plugins_dir,
    )

    print("[*] Active plugin Rank Math (seo-by-rank-math)")
    wp_cli(docroot, "plugin activate seo-by-rank-math || wp plugin activate wp-seo-rank-math")


def setup_flatsome_themes(docroot: str):
    print("[*] Cài đặt flatsome & flatsome-child")

    themes_dir = f"{docroot}/wp-content/themes"
    ssh_exec(f"mkdir -p {themes_dir}")

    # Flatsome main theme
    download_and_extract(
        url=FLATSOME_THEME_URL,
        tmp_name_default="flatsome-theme.zip",
        dest_dir=themes_dir,
        work_dir=themes_dir,
    )

    # Flatsome child
    download_and_extract(
        url=FLATSOME_CHILD_THEME_URL,
        tmp_name_default="flatsome-child.zip",
        dest_dir=themes_dir,
        work_dir=themes_dir,
    )

    print("[*] Active theme flatsome-child")
    wp_cli(docroot, "theme activate flatsome-child || wp theme activate flatsome")

# =====================================================
# ========== CẤU HÌNH AIOS TỪ FILE JSON ===============
# =====================================================

def configure_aios_from_cdn(docroot: str):
    if not AIOS_CONFIG_URL:
        print("[=] AIOS_CONFIG_URL rỗng, bỏ qua cấu hình AIOS.")
        return

    print("[*] Bắt đầu cấu hình AIOS từ CDN:", AIOS_CONFIG_URL)

    out, err = wp_cli(docroot, "plugin is-active all-in-one-wp-security-and-firewall || echo 'NOT_ACTIVE'")
    if "NOT_ACTIVE" in (out + err):
        print("[=] Plugin AIOS chưa active, bỏ qua áp dụng cấu hình.")
        return

    cmd_download = (
        f"cd {docroot} && "
        "rm -f /tmp/aois.json && "
        f"wget -O /tmp/aois.json '{AIOS_CONFIG_URL}'"
    )
    ssh_exec(cmd_download)

    cmd_update = (
        f"cd {docroot} && "
        "wp option update aio_wp_security_configs \"$(cat /tmp/aois.json)\" --format=json"
    )
    out, err = ssh_exec(cmd_update)
    if "Error" in (out + err):
        print("[!] Có thể lỗi khi update option AIOS, vui lòng kiểm tra lại log ở trên.")
    else:
        print("[+] ĐÃ ÁP DỤNG CẤU HÌNH AIOS TỪ aois.json THÀNH CÔNG.")

# =====================================================
# ======= CÀI ĐẶT CÁC PLUGIN TUỲ CHỌN (CÓ as_mu) =====
# =====================================================

def install_optional_plugins(docroot: str):
    if not OPTIONAL_PLUGINS:
        print("[=] Không có OPTIONAL_PLUGINS nào, bỏ qua.")
        return

    print("[*] Bắt đầu cài đặt plugin tuỳ chọn (OPTIONAL_PLUGINS)")
    aios_present_and_installed = False

    for p in OPTIONAL_PLUGINS:
        name = p.get("name", "Plugin không tên")
        slug = p.get("slug")
        zip_url = p.get("zip_url")
        as_mu = bool(p.get("as_mu", False))

        print(f"--- Plugin tuỳ chọn: {name} ---")

        installed_ok = False

        if slug:
            cmd = f"plugin install {slug} --activate"
            out, err = wp_cli(docroot, cmd)
            if "Error:" in (out + err):
                print(f"[!] Lỗi cài plugin {name} ({slug}) từ repo. Thử fallback zip_url nếu có.")
            else:
                print(f"[+] Đã cài & active plugin {name} ({slug}) từ repo")
                installed_ok = True
            if slug == "all-in-one-wp-security-and-firewall" and installed_ok:
                aios_present_and_installed = True

        if (not installed_ok) and zip_url:
            print(f"[*] Tải plugin {name} từ {zip_url}")
            filename = "optional-plugin-" + rand_string(6) + ".zip"
            cmd_dl = (
                f"cd {docroot} && "
                f"rm -f /tmp/{filename} && "
                f"wget -O /tmp/{filename} '{zip_url}'"
            )
            ssh_exec(cmd_dl)

            install_cmd = f"plugin install /tmp/{filename} --activate"
            out, err = wp_cli(docroot, install_cmd)
            if "Error:" in (out + err):
                print(f"[!] Lỗi cài plugin {name} từ file zip. Vui lòng kiểm tra log.")
            else:
                print(f"[+] Đã cài & active plugin {name} từ zip: {zip_url}")
                installed_ok = True

            if installed_ok and ("all-in-one-wp-security-and-firewall" in zip_url or slug == "all-in-one-wp-security-and-firewall"):
                aios_present_and_installed = True

        if not slug and not zip_url:
            print("[=] Plugin này không có slug cũng không có zip_url, bỏ qua.")
            installed_ok = False

        if installed_ok and as_mu:
            print(f"[=] {name} được đánh dấu as_mu, sẽ được đưa vào force-plugins.php")

    if aios_present_and_installed:
        print("[*] Phát hiện plugin AIOS trong OPTIONAL_PLUGINS, tiến hành cấu hình từ CDN.")
        configure_aios_from_cdn(docroot)
    else:
        print("[=] Không có plugin AIOS trong OPTIONAL_PLUGINS hoặc không cài được, bỏ qua cấu hình AIOS.")

# =====================================================
# ===== TẠO MU-PLUGIN ÉP LOAD PLUGIN as_mu ============
# =====================================================

def generate_force_plugins_mu(docroot: str):
    """
    Tạo file wp-content/mu-plugins/force-plugins.php
    để luôn luôn load các plugin được đánh dấu as_mu=True
    trong OPTIONAL_PLUGINS.
    """
    wp_content = f"{docroot}/wp-content"
    mu_plugins_dir = f"{wp_content}/mu-plugins"
    force_file = f"{mu_plugins_dir}/force-plugins.php"

    force_entries = []
    for p in OPTIONAL_PLUGINS:
        if not p.get("as_mu"):
            continue
        slug = p.get("slug")
        main_file = p.get("main_file")
        name = p.get("name", slug or "Unknown")

        if not slug or not main_file:
            print(f"[!] Plugin as_mu nhưng thiếu slug hoặc main_file: {name}")
            continue

        entry = f"""// {name}
$__path = WP_CONTENT_DIR . '/plugins/{slug}/{main_file}';
if ( file_exists( $__path ) ) {{
    include_once $__path;
}}
"""
        force_entries.append(entry)

    if not force_entries:
        print("[=] Không có plugin as_mu hợp lệ để tạo force-plugins.php, bỏ qua.")
        return

    php_content = """<?php
/**
 * Plugin Name: Force Load Critical Plugins
 * Description: Tự động load các plugin quan trọng dưới dạng Must-Use, không thể deactivate trong Admin.
 * Author: Auto Script
 * Version: 1.0
 */

// AUTO GENERATED, DO NOT EDIT MANUALLY.

"""

    php_content += "\n".join(force_entries)

    escaped = php_content.replace("\\", "\\\\").replace("'", "'\"'\"'")
    cmd = (
        f"mkdir -p {mu_plugins_dir} && "
        f"printf '{escaped}' > {force_file} && "
        f"chmod 0644 {force_file}"
    )
    ssh_exec(cmd)
    print(f"[+] Đã tạo/ghi file MU: {force_file}")

# =====================================================
# ===== TẢI .htaccess TỪ CDN (htaccess.txt) ===========
# =====================================================

def download_htaccess_from_cdn(docroot: str):
    """
    Tải nội dung từ HTACCESS_CDN_URL (htaccess.txt) về server
    và lưu thành file .htaccess trong document_root.
    Nếu đã tồn tại .htaccess sẽ GHI ĐÈ.
    """
    if not HTACCESS_CDN_URL:
        print("[=] HTACCESS_CDN_URL rỗng, bỏ qua tạo .htaccess.")
        return

    print(f"[*] Tải .htaccess từ CDN: {HTACCESS_CDN_URL}")
    htaccess_tmp = "/tmp/htaccess.txt"
    htaccess_path = f"{docroot}/.htaccess"

    cmd = (
        f"cd {docroot} && "
        f"rm -f {htaccess_tmp} && "
        f"wget -O {htaccess_tmp} '{HTACCESS_CDN_URL}' && "
        f"cp {htaccess_tmp} .htaccess && "
        f"chmod 0644 .htaccess"
    )

    out, err = ssh_exec(cmd)

    # Kiểm tra sơ bộ
    if "ERROR" in (out + err) or "failed" in (out + err).lower():
        print("[!] Có thể lỗi khi tải / copy htaccess.txt, vui lòng kiểm tra log ở trên.")
    else:
        print(f"[+] Đã tải và ghi .htaccess tại: {htaccess_path}")

# =====================================================
# ==============  CÀI WORDPRESS (WP-CLI) ==============
# =====================================================

def install_wordpress_for_domain(domain: str, document_root: str):
    cfg = get_wp_config_for_domain(domain)
    if not cfg:
        print(f"[=] Không có cấu hình WordPress cho domain {domain}, bỏ qua cài WP.")
        return {
            "status": "skipped",
            "stage": "config",
            "message": "Không có cấu hình WordPress cho domain",
        }

    print(f"\n=== BẮT ĐẦU CÀI WORDPRESS CHO {domain} ===")
    print("DocumentRoot:", document_root)

    ssh_exec(f"mkdir -p {document_root}")

    full_db_name = f"{CPANEL_USER}_{cfg['db_name']}"
    full_db_user = f"{CPANEL_USER}_{cfg['db_user']}"
    db_pass = cfg["db_pass"]

    # 1. core download
    print("[*] WP-CLI: core download")
    out, err = wp_cli(document_root, "core download")
    if "wp: command not found" in (out + err).lower():
        msg = "WP-CLI không được cài (wp command not found)."
        print("[!] Lỗi:", msg)
        return {
            "status": "error",
            "stage": "wp-cli",
            "message": msg,
        }

    # 2. config create
    print("[*] WP-CLI: config create")
    wp_cli(
        document_root,
        (
            f"config create "
            f"--dbname='{full_db_name}' "
            f"--dbuser='{full_db_user}' "
            f"--dbpass='{db_pass}' "
            f"--dbhost='{DB_HOST}' "
            f"--skip-check"
        ),
    )

    # 3. core install
    print("[*] WP-CLI: core install")
    install_cmd = (
        f"core install "
        f"--url='https://{domain}' "
        f"--title='{cfg['site_title']}' "
        f"--admin_user='{cfg['wp_user']}' "
        f"--admin_password='{cfg['wp_pass']}' "
        f"--admin_email='{cfg['wp_email']}' "
        f"--skip-email"
    )
    wp_cli(document_root, install_cmd)

    # 4. TẮT INDEX: blog_public = 0  (Discourage search engines)
    print("[*] WP-CLI: set Search Engine Visibility = OFF (blog_public = 0)")
    wp_cli(document_root, "option update blog_public 0")

    print(f"[+] ĐÃ CÀI WORDPRESS THÀNH CÔNG CHO {domain}")
    print(f"    URL       : https://{domain}")
    print(f"    Admin 1   : {cfg['wp_user']} / {cfg['wp_pass']}")
    print(f"    DB        : {full_db_name}")
    print(f"    DB User   : {full_db_user}")
    print(f"    DB Pass   : {db_pass}")

    # 5. Tạo admin 2 (nếu có cấu hình)
    if cfg.get("wp_user2") and cfg.get("wp_pass2"):
        print("[*] WP-CLI: tạo admin user thứ 2")
        user2_cmd = (
            f"user create '{cfg['wp_user2']}' 'admin2@{domain}' "
            f"--role=administrator --user_pass='{cfg['wp_pass2']}'"
        )
        wp_cli(document_root, user2_cmd)
        print(f"[+] ĐÃ TẠO ADMIN 2: {cfg['wp_user2']} / {cfg['wp_pass2']}")

    # 6. Plugin / theme / harden
    setup_mu_plugins_and_rankmath(document_root)
    setup_flatsome_themes(document_root)
    install_optional_plugins(document_root)
    harden_wp_config_if_needed(document_root, cfg.get("is_lock_file", False))

    # 7. Tạo MU plugin ép load các plugin as_mu
    generate_force_plugins_mu(document_root)

    # 8. Tải file .htaccess từ CDN (htaccess.txt) và ghi đè
    download_htaccess_from_cdn(document_root)

    print("=" * 70 + "\n")

    return {
        "status": "success",
        "stage": "completed",
        "message": "Cài WordPress + plugin + theme + .htaccess (từ CDN) thành công",
        "admin_user": cfg["wp_user"],
        "admin_pass": cfg["wp_pass"],
        "db_name": full_db_name,
        "db_user": full_db_user,
    }

# =====================================================
# ==============  MAIN  ===============================
# =====================================================

def main():
    if not test_login_api2():
        print("\n[!] Dừng lại vì login API2 chưa OK.")
        return

    print("\n=== BẮT ĐẦU TẠO ADDON DOMAINS & CÀI WORDPRESS ===")
    print("DOMAINS_BASE_DIR =", repr(DOMAINS_BASE_DIR))

    results = []

    for d in ADDON_DOMAINS:
        domain_result = {
            "domain": d,
            "status": "unknown",
            "stage": "",
            "message": "",
            "document_root": "",
        }
        try:
            document_root = create_addon_domain_api2(d)
            if not document_root:
                msg = "Không có document_root hợp lệ (tạo addon domain lỗi)."
                print(f"[!] Bỏ qua cài WP cho {d}: {msg}")
                domain_result.update({
                    "status": "error",
                    "stage": "addon",
                    "message": msg,
                })
                results.append(domain_result)
                continue

            domain_result["document_root"] = document_root

            wp_result = install_wordpress_for_domain(d, document_root)
            if not wp_result:
                domain_result.update({
                    "status": "error",
                    "stage": "wp-cli",
                    "message": "Không rõ (install_wordpress_for_domain trả None)",
                })
            else:
                domain_result.update(wp_result)

        except Exception as e:
            err_msg = str(e)
            print(f"[!] Lỗi không mong muốn khi xử lý domain {d}: {err_msg}")
            domain_result.update({
                "status": "error",
                "stage": "exception",
                "message": err_msg,
            })

        results.append(domain_result)

    print("\n\n================= TỔNG KẾT DOMAIN =================")
    header = (
        f"{'Domain':30} {'Status':10} {'Stage':10} "
        f"{'Admin user':15} {'Admin pass':22} "
        f"{'DB name':24} {'DB user':24} {'Docroot'}"
    )
    print(header)
    print("-" * len(header))

    for r in results:
        domain = r["domain"]
        status = r.get("status", "")
        stage = r.get("stage", "")
        admin_user = r.get("admin_user", "")
        admin_pass = r.get("admin_pass", "")
        db_name = r.get("db_name", "")
        db_user = r.get("db_user", "")
        docroot = r.get("document_root", "")

        print(
            f"{domain:30} {status:10} {stage:10} "
            f"{admin_user:15} {admin_pass:22} "
            f"{db_name:24} {db_user:24} {docroot}"
        )

    print("\nGhi chú: chi tiết lỗi / message đã in ở log từng domain ở phía trên.")


if __name__ == "__main__":
    main()
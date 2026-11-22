---
name: pbn-site-provision
description: Quy trình chuẩn cài đặt trọn gói website PBN WordPress mới (trỏ Cloudflare DNS, add site vào aaPanel/cPanel + MySQL, cài WP core, user mặc định ad_official + user phụ, mu-plugins chuẩn Dual Manager, wp-seo-rank-math, litespeed-cache, OPTIONAL_PLUGINS + force-plugins.php + AIOS aois.json, theme Flatsome + Flatsome Child, khóa chattr +i và đồng bộ Dashboard V2). Kích hoạt khi user yêu cầu cài site mới, add site vào aaPanel/CF, hoặc cài bộ plugin/theme chuẩn PBN.
---

# PBN New Site Provisioning & Standard Stack Skill

Skill này quy chuẩn toàn bộ các bước từ A-Z khi tạo và cài đặt website WordPress PBN mới trên hệ thống **aaPanel/VPS** (hoặc cPanel), đảm bảo đầy đủ cấu hình bảo mật, tối ưu cache, theme, plugin và kết nối với PBN Dashboard V2 (`https://pbn.keodinh.net/`).

---

## 1. Cấu Hình Cloudflare DNS
1. Tra cứu tài khoản Cloudflare từ bảng `settings` (`key = 'cf_accounts'`) trong `PBN-Dashboard-V2/pbn_matrix.db` (hiện có tài khoản `admin` / `baychulun@happinc.info` và `tp` / `vnae88888886@gmail.com`).
2. Với mỗi domain:
   - Nếu Zone chưa tồn tại trên Cloudflare, gọi `POST /zones` (`type: "full"`) để thêm Zone và lấy 2 Nameserver báo lại cho user trỏ ở registrar.
   - Tạo hoặc cập nhật 2 bản ghi **A**:
     - `<domain>` $\rightarrow$ IP server đích (`proxied: true`, `ttl: 1`)
     - `www.<domain>` $\rightarrow$ IP server đích (`proxied: true`, `ttl: 1`)
   - Đảm bảo chế độ SSL Cloudflare đặt `flexible` (`PATCH /zones/{id}/settings/ssl` = `{"value": "flexible"}`) nếu server dùng OpenLiteSpeed cổng `80` (hoặc `full` nếu đã cài SSL riêng trên vhost).

---

## 2. Tạo Site & Database Trên Server

### A. Trên aaPanel / VPS (OpenLiteSpeed + PHP 8.3 + MySQL)
- Gọi trực tiếp `panelSite.panelSite().AddSite(get)` bằng `/www/server/panel/pyenv/bin/python` (tránh lỗi whitelist IP của panel HTTP API):
  - `webname`: `{"domain": "<domain>", "domainlist": ["www.<domain>"], "count": 0}`
  - `path`: `/www/wwwroot/<domain>`
  - `type`: `"PHP"`, `version`: `"83"`, `port`: `"80"`, `set_ssl`: `"0"`, `redirect`: `""`
  - `sql`: `"MySQL"`, `codeing`: `"utf8mb4"`, `datauser` ($\le 16$ ký tự, ví dụ `wp_<slug>`), `datapassword` (chuỗi ngẫu nhiên 16 ký tự alnum).
- Xóa file `index.html` mặc định do aaPanel sinh ra trước khi cài WordPress.

### B. Trên cPanel
- Dùng API2 `AddonDomain::addaddondomain` và UAPI `Mysql` (`create_database`, `create_user`, `set_privileges_on_database`) tương tự `PBN-Dashboard-V2/VPS-client/13-cai-plugin-sites.py`.

---

## 3. Cài Đặt WordPress Core, Tài Khoản & Hardening

1. **WP Core & Database**:
   - **Lưu ý quan trọng**: PHP CLI trên aaPanel mặc định `memory_limit=128M`, dễ lỗi OOM khi `wp-cli` giải nén/cài plugin; luôn chạy `php -d memory_limit=512M /usr/local/bin/wp --allow-root ...` (hoặc tải `https://wordpress.org/latest.tar.gz` một lần rồi `cp` vào từng site).
   - `wp core download --locale=en_US --force`
   - `wp config create --dbname=... --dbuser=... --dbpass=... --dbhost=localhost --skip-check`
   - `wp core install --url=https://<domain> --title=<domain> --admin_user=ad_official --admin_password='seFQv)TR*h9Itlec!Gc*v)c*' --admin_email=admin@<domain> --skip-email`
   - Mặc định set `wp option update blog_public 0` (tắt index khi mới dựng; chỉ mở `1` khi có nội dung hoặc user yêu cầu).

2. **Tài khoản Admin mặc định & bổ sung**:
   - **User mặc định luôn phải có**:
     - Username: `ad_official`
     - Password: `seFQv)TR*h9Itlec!Gc*v)c*`
     - Role: `administrator`
   - **User bổ sung (theo từng yêu cầu cụ thể của user)**:
     - Ví dụ đợt 18/11/2026: Username `owen` / Password `*Fe4Gpnm` / Role `administrator`.
   - *Lưu ý kỹ thuật*: Mật khẩu có ký tự đặc biệt (`*`, `)`, `!`), khi chạy `wp-cli` phải truyền qua `subprocess` list args hoặc script Python cục bộ trên server, tuyệt đối không nối chuỗi shell thô.

3. **Cấu hình `wp-config.php`** (theo `update-nwm-khoa-file-xuat-csv-Khong-SSH.py`):
   Chèn ngay sau `<?php` nếu chưa có:
   ```php
   ini_set('display_errors','Off');
   ini_set('error_reporting', E_ALL );
   define('FS_METHOD', 'direct');
   ```

4. **File `.htaccess` & Chặn `xmlrpc.php`**:
   - Tải từ CDN: `https://cdn.keodinh.net/wp/htaccess.txt` ghi ra `.htaccess`.
   - Bổ sung đầu file rule chặn `xmlrpc.php` cho cả Apache và OpenLiteSpeed (nếu chưa có):
     ```apache
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
     ```

---

## 4. Bộ MU-Plugins, Plugins Bắt Buộc & Theme

### A. Plugins & Cấu Hình Chuẩn
1. **Rank Math Custom (`wp-seo-rank-math`)**:
   - Tải & giải nén `http://cdn.keodinh.net/wp/wp-seo-rank-math.tar.gz?ss=77` vào `wp-content/plugins/`.
   - Kích hoạt: `wp plugin activate wp-seo-rank-math --skip-plugins --skip-themes`.
2. **LiteSpeed Cache (`litespeed-cache`)**:
   - Cài & kích hoạt từ WordPress.org: `wp plugin install litespeed-cache --activate --force`.
3. **OPTIONAL_PLUGINS chuẩn (có hỗ trợ `as_mu` + phiên bản cụ thể)**:
   - **Pretty Links** (`slug`: `pretty-link`, `zip_url`: `https://downloads.wordpress.org/plugin/pretty-link.3.6.19.zip`, `as_mu`: `True`, `main_file`: `pretty-link.php`)
   - **All In One WP Security & Firewall** (`slug`: `all-in-one-wp-security-and-firewall`, `zip_url`: `https://downloads.wordpress.org/plugin/all-in-one-wp-security-and-firewall.5.4.4.zip`, `as_mu`: `True`, `main_file`: `wp-security.php`)
     - Sau khi active AIOS, tải `https://cdn.keodinh.net/wp/aois.json` và nạp cấu hình:
       ```bash
       wp option update aio_wp_security_configs "$(cat /tmp/aois.json)" --format=json
       ```
   - *(Nếu user yêu cầu cài thêm plugin khác ở các lần sau, thêm vào danh sách cài đặt và cập nhật `force-plugins.php` nếu được đánh dấu `as_mu: True`)*.

### B. MU-Plugins (Sau khi kích hoạt xong các plugin ở mục A)
1. **Base MU (`init.php`)**: **KHÔNG tải từ CDN** (`mu-plugins.zip` / `mu-plugins.tar.gz`) nữa — copy trực tiếp từ file chuẩn trong repo `mu-plugins/init.php` (đã xóa comment & mã hóa Base64) vào `wp-content/mu-plugins/init.php`.
2. **Manager Plugin (TUÂN THỦ DUAL MANAGER RULE)**:
   - **aaPanel / VPS**: Copy bản mới nhất `PBN-Dashboard-V2/p-manager.php` (Base64 encoded) vào `wp-content/mu-plugins/p-manager.php`.
   - **cPanel**: Copy bản mới nhất `PBN-Dashboard-V2/p-manager-u.php` (Plain PHP ẩn danh) vào `wp-content/mu-plugins/p-manager-u.php` và xóa `p-manager.php`.
3. **MU Loader cho Rank Math (`wp-content/mu-plugins/wp-seo-rank-math.php`)**:
   ```php
   <?php
   /*
   Plugin Name: Rank Math SEO Plugin. (MU Loader)
   */
   if (file_exists(ABSPATH . 'wp-content/plugins/wp-seo-rank-math/wp-seo-rank-math.php')) {
       require_once ABSPATH . 'wp-content/plugins/wp-seo-rank-math/wp-seo-rank-math.php';
   }
   ```
4. **Ép chạy `as_mu` (`wp-content/mu-plugins/force-plugins.php`)**:
   Tự động `include_once` `WP_CONTENT_DIR . '/plugins/<slug>/<main_file>'` cho các plugin đánh dấu `as_mu: True` (`pretty-link/pretty-link.php`, `all-in-one-wp-security-and-firewall/wp-security.php`).

### C. Theme Flatsome + Child Theme
1. Tải & giải nén `http://cdn.keodinh.net/wp/flatsome.3.20.4.zip` (hoặc `flatsome-3.15.3.zip` nếu được chỉ định) vào `wp-content/themes/`.
2. Tải & giải nén `http://cdn.keodinh.net/wp/flatsome-child.zip` vào `wp-content/themes/`.
3. Kích hoạt child theme: `wp theme activate flatsome-child`.

---

## 5. Khóa File Theo Kịch Bản & Hoàn Tất

1. **Phân quyền & Khóa `chattr` trên aaPanel/VPS** (theo `update-nwm-khoa-file-xuat-csv-Khong-SSH.py`):
   ```bash
   chown -R www:www "$root"
   chown root:root "$root/.user.ini" 2>/dev/null || true
   chattr +i "$root/.user.ini" 2>/dev/null || true

   cd "$root" || exit 1
   chattr +i .
   [ -d wp-content ] && chattr -i wp-content && chattr -i -R wp-content
   [ -f wp-config.php ] && chattr -i wp-config.php
   [ -f .htaccess ] && chattr -i .htaccess
   [ -f aios-bootstrap.php ] && chattr -i aios-bootstrap.php
   ```
2. **Reload Web Server & PHP**:
   ```bash
   killall -9 lsphp 2>/dev/null || true
   /usr/local/lsws/bin/lswsctrl reload 2>/dev/null || true
   ```
3. **Đồng bộ vào Dashboard V2 (`103.106.105.77` `pbn_matrix.db`)**:
   Insert/upsert các domain mới vào bảng `sites` (`server_id`, `ip`, `approval_status='approved'`, `is_noindex`).
4. **Nghiệm thu Live**:
   - Kiểm tra trang chủ (`HTTP 200`), endpoint manager (`POST https://<domain>/?ttpp=atc=getindex`), kiểm tra theme đang active là `flatsome-child`, kiểm tra user `ad_official` + user phụ đăng nhập được.

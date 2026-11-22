# Hướng Dẫn & Quy Chuẩn Cài Đặt Website WordPress PBN Mới

> Tài liệu này tổng hợp đầy đủ các yêu cầu chuẩn khi dựng và cấu hình một website WordPress vệ tinh (PBN) trên hệ thống aaPanel (VPS) hoặc cPanel, đồng bộ với skill kỹ thuật tại `.agents/skills/pbn-site-provision/SKILL.md`.

---

## 1. Cấu Hình Tên Miền Trên Cloudflare
- **Tài khoản Cloudflare**: Lưu trong `PBN-Dashboard-V2/pbn_matrix.db` (`settings.cf_accounts`, hiện gồm tài khoản `admin` - `baychulun@happinc.info` và `tp` - `vnae88888886@gmail.com`).
- **Quy tắc trỏ DNS**:
  - Nếu domain chưa có trên Cloudflare: Thêm Zone mới (`POST /zones`) và gửi lại 2 Nameserver cho chủ hệ thống trỏ ở nhà cung cấp tên miền (GoDaddy, Namecheap...).
  - Tạo 2 bản ghi **A**:
    - `@` (root domain) $\rightarrow$ IP server đích (`Proxied = True`)
    - `www` $\rightarrow$ IP server đích (`Proxied = True`)
  - Thiết lập **SSL/TLS**: Chọn `Flexible` nếu vhost server chạy cổng `80` (OpenLiteSpeed mặc định trên hệ thống), hoặc `Full` nếu có chứng chỉ SSL riêng trên server.

---

## 2. Tạo Website & Database Trên Server

### A. Trên aaPanel / VPS (OpenLiteSpeed + PHP 8.3 + MySQL)
- Add đúng domain (kèm `www.<domain>`) vào aaPanel qua API nội bộ `panelSite.AddSite` (hoặc giao diện aaPanel):
  - Document Root: `/www/wwwroot/<domain>`
  - PHP Version: `PHP-83`
  - Port: `80`
  - Tạo sẵn Database MySQL (`utf8mb4`), đặt tên & user $\le 16$ ký tự theo dạng `wp_<slug>`.
- Xóa file `index.html` mặc định của aaPanel trước khi cài WordPress.

### B. Trên cPanel
- Tạo Addon Domain qua API2 (`AddonDomain::addaddondomain`) và tạo MySQL Database/User + phân quyền `ALL PRIVILEGES` qua UAPI (`Mysql`).

---

## 3. Cài Đặt WordPress Core & Tài Khoản Quản Trị

1. **Cài đặt WP Core** *(chú ý chạy `php -d memory_limit=512M /usr/local/bin/wp --allow-root` để tránh lỗi hết RAM 128M của PHP CLI)*:
   - Tải WordPress Core mới nhất (`https://wordpress.org/latest.tar.gz`), tạo `wp-config.php` và cài site qua WP-CLI.
   - Đặt mặc định chặn index khi mới dựng: `blog_public = 0` (sau này khi lên nội dung xong sẽ mở `1` bằng nút Mở Index trên Dashboard V2).

2. **Tài khoản User mặc định & User phụ**:
   - **Tài khoản Admin mặc định (LUÔN PHẢI CÓ trên mọi site)**:
     - **Username**: `ad_official`
     - **Password**: `seFQv)TR*h9Itlec!Gc*v)c*`
     - **Role**: `administrator`
   - **User phụ / User theo từng đợt yêu cầu**:
     - Sẽ tạo thêm theo yêu cầu cụ thể mỗi lần cài (ví dụ: `owen` / `*Fe4Gpnm`, role `administrator`).

3. **Cấu hình `wp-config.php`**:
   Thêm các dòng sau ngay dưới `<?php`:
   ```php
   ini_set('display_errors','Off');
   ini_set('error_reporting', E_ALL );
   define('FS_METHOD', 'direct');
   ```

4. **Cấu hình `.htaccess` & Chặn `xmlrpc.php`**:
   - Tải nội dung chuẩn từ CDN: `https://cdn.keodinh.net/wp/htaccess.txt` lưu thành `.htaccess`.
   - Bổ sung rule chặn tấn công `xmlrpc.php` cho cả Apache và OpenLiteSpeed:
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

## 4. Bộ Theme & Plugins Chuẩn Bắt Buộc

### A. Theme Flatsome + Child Theme
- **Theme cha (`flatsome`)**: Tải từ `http://cdn.keodinh.net/wp/flatsome.3.20.4.zip` (hoặc phiên bản được chỉ định).
- **Child theme (`flatsome-child`)**: Tải từ `http://cdn.keodinh.net/wp/flatsome-child.zip`.
- **Kích hoạt**: Bắt buộc **active `flatsome-child`** (`wp theme activate flatsome-child`).

### B. Plugins Chính & `OPTIONAL_PLUGINS`
1. **WP SEO Rank Math bản custom (`wp-seo-rank-math`)**:
   - Tải từ `http://cdn.keodinh.net/wp/wp-seo-rank-math.tar.gz?ss=77`, giải nén vào `wp-content/plugins/` và kích hoạt.
2. **LiteSpeed Cache (`litespeed-cache`)**:
   - Cài đặt bản mới nhất từ kho WordPress và kích hoạt (`wp plugin install litespeed-cache --activate`).
3. **Danh sách `OPTIONAL_PLUGINS` (hỗ trợ `as_mu` + `force-plugins.php`)**:
   - **Pretty Links** (`3.6.19`):
     - `slug`: `pretty-link`
     - `zip_url`: `https://downloads.wordpress.org/plugin/pretty-link.3.6.19.zip`
     - `as_mu`: `True`, `main_file`: `pretty-link.php`
   - **All In One WP Security & Firewall (AIOS)** (`5.4.4`):
     - `slug`: `all-in-one-wp-security-and-firewall`
     - `zip_url`: `https://downloads.wordpress.org/plugin/all-in-one-wp-security-and-firewall.5.4.4.zip`
     - `as_mu`: `True`, `main_file`: `wp-security.php`
     - **Cấu hình tự động AIOS**: Tải `https://cdn.keodinh.net/wp/aois.json` và nạp vào option `aio_wp_security_configs` (`--format=json`).
   - *(Nếu các lần sau có yêu cầu cài thêm plugin mới, chỉ cần thêm vào danh sách cài đặt và khai báo `as_mu: True` nếu muốn ép chạy ngầm không tắt được).*

### C. Thư mục `wp-content/mu-plugins/` (Tuân thủ Dual Manager & Whitelist)
1. **`init.php`**: **KHÔNG tải từ CDN** (`mu-plugins.zip?dd=44` / `mu-plugins.tar.gz`) nữa — lấy trực tiếp từ `mu-plugins/init.php` trong workspace (đã xóa hết comment giải thích và mã hóa Base64, chứa hook bảo vệ user `ad_official`, ẩn/khóa cài plugin mới sau 7 ngày, danh sách whitelist...).
2. **Manager Plugin (phân biệt theo loại server)**:
   - **Nếu là aaPanel / VPS**: Upload bản **`PBN-Dashboard-V2/p-manager.php`** (mã hóa Base64 mới nhất).
   - **Nếu là cPanel**: Upload bản **`PBN-Dashboard-V2/p-manager-u.php`** (Plain PHP đã ẩn IP/domain máy chủ mẹ để tránh Imunify360 xóa về 0 bytes) và xóa `p-manager.php` cũ nếu có.
3. **`wp-seo-rank-math.php`**: File MU loader tự nạp `wp-content/plugins/wp-seo-rank-math/wp-seo-rank-math.php`.
4. **`force-plugins.php`**: Tự động sinh để ép load dưới dạng Must-Use tất cả các plugin có `as_mu: True` trong `OPTIONAL_PLUGINS` (`pretty-link/pretty-link.php`, `all-in-one-wp-security-and-firewall/wp-security.php`).

---

## 5. Cơ Chế Khóa File & Khóa Cài Plugin Mới

### A. Khóa file trên VPS (`chattr +i` theo kịch bản `update-nwm-khoa-file-xuat-csv-Khong-SSH.py`)
- Phân quyền chuẩn `chown -R www:www <root>` (riêng `.user.ini` giữ `root:root` + `chattr +i`).
- Khóa thư mục gốc `chattr +i .` để chống tạo file PHP rác/mã độc ngoài root.
- **Mở khóa (`chattr -i`)** cho các thành phần WordPress cần ghi dữ liệu/cache:
  - `wp-content` (và toàn bộ thư mục con `-R`)
  - `wp-config.php`, `.htaccess`, `aios-bootstrap.php`

### B. Lưu ý về tính năng khóa cài plugin mới trong `init.php`
- Theo thiết kế trong `init.php`, khi site mới cài lần đầu, `init.php` lưu mốc `nwm_first_visit_time` và **chỉ tự động bật khóa (`nwm_restricted_plugin_mode = enable`) sau 7 ngày (1 tuần)** để chủ web có thời gian setup ban đầu.
- Nếu muốn **ép khóa ngay lập tức** sau khi cài xong mà không chờ 7 ngày:
  - Gọi URL kích hoạt: `https://<domain>/?nwm_save=1&key=nwmmml17wWzzSiaowislkdjfnx&mode=enable`
  - Hoặc chạy WP-CLI: `wp option update nwm_restricted_plugin_mode enable && wp option update nwm_restricted_plugin_scope all`
- Nếu muốn **mở khóa lại** để cài thêm plugin:
  - `https://<domain>/?nwm_save=1&key=nwmmml17wWzzSiaowislkdjfnx&mode=disable&scope=all` (mở hết) hoặc `&scope=part` (mở nhưng vẫn chặn nhóm backup/file manager).

---

## 6. Đồng Bộ & Nghiệm Thu Cuối
1. Reload `lsphp` và OpenLiteSpeed (`killall -9 lsphp`, `lswsctrl reload`).
2. Đồng bộ danh sách domain mới vào database `pbn_matrix.db` trên server trung tâm `103.106.105.77` để quản lý trên `https://pbn.keodinh.net/`.
3. Kiểm tra thực tế:
   - Truy cập trang chủ trả `HTTP 200`, giao diện đang chạy `flatsome-child`.
   - Test `POST https://<domain>/?ttpp=atc=getindex` trả JSON hợp lệ từ `p-manager`.
   - Test `xmlrpc.php` đã bị chặn (`403` / `405`).

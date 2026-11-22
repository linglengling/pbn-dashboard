# PBN MANAGEMENT DASHBOARD — TÀI LIỆU ĐẶC TẢ TOÀN BỘ LOGIC HỆ THỐNG (SYSTEM SPECIFICATION)

> **Phiên bản**: V2 (Python Native Engine)  
> **Mục tiêu**: Bộ não điều khiển tập trung toàn bộ mạng lưới site PBN (WordPress) trên nhiều cụm máy chủ (aaPanel VPS, cPanel Hosting).

---

## 1. KIẾN TRÚC TỔNG THỂ & DÒNG CHẢY DỮ LIỆU (DATA FLOW)

```
       [ 1,000+ WordPress PBN Sites ]
         │ (Tự động gửi Ping heartbeat qua WS 9090 hoặc HTTP POST)
         │ (Nhận lệnh tạo bài, đặt backlink, chèn script qua REST API)
         ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   BỘ NÃO TRUNG TÂM (PBN DASHBOARD V2)                 │
│                                                                        │
│  [FastAPI Core Server :5555]                                           │
│   ├── JWT Auth & User Management (PBKDF2/SHA256, 7-day token)          │
│   ├── Gzip Compression Middleware (Giảm 93% payload qua mạng)         │
│   ├── Static SPA Server (React 18 Dashboard đa ngôn ngữ VI/EN/ZH)      │
│   ├── WebSocket Hub (:9090 & /ws realtime events)                      │
│   │                                                                    │
│   ├── Module Sites: Duyệt site, ping monitor, link checker             │
│   ├── Module Servers: Quét SSH, cPanel UAPI, auto-deploy mu-plugins    │
│   ├── Module Backlinks: Bơm backlink vào bài viết, kiểm tra index      │
│   ├── Module AI Writer: Tự động viết bài chuẩn SEO, đóng watermark     │
│   └── Module Logs & Metrics: Thống kê trạng thái toàn hệ thống         │
│                                                                        │
│  [CSDL Cục bộ SQLite - `pbn_matrix.db` (WAL Mode)]                     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Thao tác quản trị hệ thống
                                    ▼
       [ Cụm Máy Chủ: aaPanel VPS & cPanel Hosting ]
         - VPS 1: 194.233.83.83 (91 WP)
         - VPS 2: 172.96.190.231 (125 WP)
         - VPS 3: 198.252.110.104 (96 WP)
         - VPS 4: 198.252.101.160 (73 WP)
         - VPS 5: 198.252.99.79 (44 WP)
         - VPS 6: 172.96.184.18 (41 WP)
         - cPanel SNG-SD120 (150 WP)
         - cPanel DAL-SD201 (111 WP)
         - cPanel TOR-SD204 (233 WP)
```

---

## 2. CƠ SỞ DỮ LIỆU CỤC BỘ (SQLITE SCHEMA)

Hệ thống sử dụng SQLite cục bộ với chế độ **WAL (Write-Ahead Logging)** để xử lý đồng thời hàng ngàn lượt đọc/ghi mỗi giây:

### 2.1. Bảng `users` (Quản trị viên)
* `id` INTEGER PRIMARY KEY AUTOINCREMENT
* `username` TEXT UNIQUE NOT NULL
* `password_hash` TEXT NOT NULL (PBKDF2-SHA256)
* `salt` TEXT NOT NULL
* `role` TEXT DEFAULT 'admin'
* `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP

### 2.2. Bảng `servers` (Quản lý cụm Server / Hosting)
* `id` INTEGER PRIMARY KEY AUTOINCREMENT
* `name` TEXT NOT NULL (vd: "VPS aaPanel 1", "cPanel SNG-SD120")
* `type` TEXT NOT NULL (`vps` hoặc `cpanel`)
* `host` TEXT NOT NULL (IP hoặc Domain hostname)
* `port` INTEGER DEFAULT 22
* `username` TEXT NOT NULL
* `password` TEXT NOT NULL
* `status` TEXT DEFAULT 'ONLINE' (`ONLINE`, `ERROR`, `SCANNING`)
* `sites_count` INTEGER DEFAULT 0
* `last_checked` DATETIME
* `error_message` TEXT
* `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP

### 2.3. Bảng `sites` (Quản lý các trang WordPress PBN)
* `domain` TEXT PRIMARY KEY
* `ip` TEXT
* `last_seen` DATETIME
* `status` TEXT DEFAULT 'ONLINE' (`ONLINE`, `OFFLINE`)
* `cluster` TEXT (Tên cụm / hostname máy chủ)
* `api_key` TEXT (Secret key xác thực giữa WP site và Dashboard)
* `site_url` TEXT (URL đầy đủ kèm https://)
* `wp_version` TEXT
* `total_homepage_links` INTEGER DEFAULT 0
* `head_code` TEXT (Script header chèn vào site)
* `homepage_outbound_links` TEXT (JSON mảng link out trang chủ)
* `approval_status` TEXT DEFAULT 'APPROVED' (`APPROVED`, `PENDING`, `REJECTED`)
* `server_id` INTEGER REFERENCES servers(id)
* `server_host` TEXT
* `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
* `updated_at` DATETIME

### 2.4. Bảng `backlinks` (Quản lý Backlink chèn vào bài)
* `id` INTEGER PRIMARY KEY AUTOINCREMENT
* `site_domain` TEXT NOT NULL
* `target_url` TEXT NOT NULL
* `anchor_text` TEXT NOT NULL
* `post_id` INTEGER
* `post_url` TEXT
* `status` TEXT DEFAULT 'ACTIVE' (`ACTIVE`, `LOST`, `ERROR`)
* `last_verified` DATETIME
* `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP

### 2.5. Bảng `posts` (Lịch sử bài viết đã đăng)
* `id` INTEGER PRIMARY KEY AUTOINCREMENT
* `site_domain` TEXT NOT NULL
* `wp_post_id` INTEGER
* `post_title` TEXT
* `post_url` TEXT
* `status` TEXT DEFAULT 'PUBLISHED'
* `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP

### 2.6. Bảng `activity_log` (Nhật ký hoạt động)
* `id` INTEGER PRIMARY KEY AUTOINCREMENT
* `target` TEXT (Domain hoặc Tên user)
* `action` TEXT (vd: 'site_ping', 'backlink_inserted', 'server_scan')
* `details` TEXT (JSON chuỗi thông tin chi tiết)
* `timestamp` DATETIME DEFAULT CURRENT_TIMESTAMP

### 2.7. Bảng `settings` (Cấu hình AI & Hệ thống)
* `key` TEXT PRIMARY KEY
* `value` TEXT

---

## 3. LOGIC HOẠT ĐỘNG CỦA CÁC MODULE

### 3.1. Module Xác Thực (Authentication & Security)
* **Thuật toán băm**: PBKDF2 với SHA256, 10,000 vòng lặp, salt ngẫu nhiên 16 bytes.
* **Thời hạn phiên**: Token JWT có hạn 7 ngày (`exp: 7 days`).
* **Tài khoản mặc định**: `admin` / `Abcd@12347` (tự động khởi tạo nếu chưa có trong DB).
* **Bảo vệ Endpoint**: Mọi API quản trị đều yêu cầu Header: `Authorization: Bearer <TOKEN>`.

---

### 3.2. Module Nhận Ping & Heartbeat từ WordPress Sites (Site Monitor)
Mỗi website WordPress khi có cài đặt `pbn-manager.php` trong thư mục `wp-content/mu-plugins/` sẽ hoạt động như sau:
1. **Khởi tạo Heartbeat**:
   * Khi có traffic hoặc qua WordPress Cron (mỗi 5-15 phút), plugin thu thập:
     - `domain`, `ip`, `site_url`, `wp_version`
     - Số lượng outbound link trên trang chủ
     - Header scripts (`head_code`)
   * Kết nối tới Dashboard qua **WebSocket port 9090** (hoặc fallback qua `POST /api/sites/ping`).
2. **Quy trình Phê duyệt Site (Approval Flow)**:
   * Nếu domain lần đầu ping về mà chưa có trong DB:
     - Lưu với trạng thái `approval_status = 'PENDING'`.
     - Bắn sự kiện realtime `site:pending` lên Dashboard báo cho admin.
   * Admin bấm **Phê duyệt (Approve)** hoặc **Từ chối (Reject)** trên Dashboard:
     - Duyệt -> Chuyển thành `approval_status = 'APPROVED'`, `status = 'ONLINE'`.
     - Từ chối -> Xóa vĩnh viễn hoặc chặn ping tiếp theo.
3. **Giám sát Trực tuyến (Online/Offline Monitor)**:
   * Chạy background loop kiểm tra: Nếu site không ping về sau **60 phút** -> Tự động chuyển `status = 'OFFLINE'`.

---

### 3.3. Module Quản Lý Cụm Server (VPS & cPanel Automation)
Sử dụng thư viện Python thuần (`paramiko`, `requests`):
1. **Kiểm tra kết nối (Test Server Connection)**:
   * Với VPS Linux (aaPanel): Kết nối SSH (port 22), chạy `hostname && uname -a`, lấy thông tin OS và user.
   * Với cPanel: Kết nối SSH hoặc cPanel UAPI port 2083, xác thực user/pass.
2. **Quét Tự Động Website WordPress (Scan Sites)**:
   * VPS: Quét lệnh `find /www/wwwroot -maxdepth 2 -name 'wp-config.php'` (và các thư mục phụ `/home`, `/var/www`).
   * cPanel: Quét `/home/<user>/public_html` và các thư mục addon domains.
   * Lấy URL chính xác bằng lệnh WP-CLI: `wp option get siteurl` (fallback trích xuất từ file `wp-config.php`).
   * Tự động lưu hoặc cập nhật danh sách site vào bảng `sites` kèm `server_id` và `server_host`.
3. **Cài Đặt Tự Động `pbn-manager.php` (Deploy mu-plugin)**:
   * Upload file `pbn-manager.php` lên `/tmp/pbn-manager.php` của máy chủ từ xa.
   * Tự động chạy lệnh:
     `mkdir -p <site_dir>/wp-content/mu-plugins && cp /tmp/pbn-manager.php <site_dir>/wp-content/mu-plugins/ && chown -R www:www <site_dir>/wp-content/mu-plugins && chmod 644 <site_dir>/wp-content/mu-plugins/pbn-manager.php`
   * Xác minh mã phản hồi trả về `Version: 1.0.0`.
   * Hỗ trợ triển khai cho 1 server hoặc **Deploy hàng loạt tất cả server** cùng 1 click.

---

### 3.4. Module Quản Lý & Chèn Backlink (Backlink Injection)
1. **Chèn Backlink Tự Động**:
   * Dashboard gửi request POST tới REST API của site con:
     `POST <site_url>/wp-json/pbn/v1/insert-link` kèm payload:
     `{ "target_url": "...", "anchor_text": "...", "post_id": 123, "api_key": "..." }`
   * Plugin `pbn-manager.php` tìm vị trí tự nhiên trong bài viết, bọc anchor text bằng thẻ `<a href="..." target="_blank" rel="follow">`, lưu bài viết và trả về `success: true`.
   * Ghi nhận vào bảng `backlinks` trạng thái `ACTIVE`.
2. **Tự Động Kiểm Tra Sống/Chết của Backlink (Backlink Verification)**:
   * Định kỳ gửi HTTP GET tải HTML của bài viết (`post_url`).
   * Kiểm tra xem thẻ `<a>` chứa `target_url` và `anchor_text` có còn tồn tại không.
   * Nếu còn -> Cập nhật `last_verified = NOW()`, `status = 'ACTIVE'`.
   * Nếu mất link -> Cập nhật `status = 'LOST'` và cảnh báo trên giao diện.

---

### 3.5. Module Viết Bài Chuẩn SEO Bằng AI & Watermark Ảnh
1. **Sinh Bài Viết Bằng AI**:
   * Hỗ trợ cấu hình OpenAI API hoặc các API tương thích (DeepSeek, Claude, v.v.).
   * Người dùng nhập từ khóa (`keyword`) + chọn danh sách site cần đăng.
   * AI tạo dàn bài (Outline) và bài viết hoàn chỉnh định dạng HTML chuẩn (h1, h2, h3, p, ul/li, context image).
2. **Đóng Dấu Bản Quyền Ảnh (Watermark Image)**:
   * Sử dụng thư viện `Pillow` (PIL) trong Python.
   * Tải ảnh gốc -> Đóng watermark chữ hoặc logo mờ góc phải dưới -> Tối ưu hóa dung lượng (WebP/JPEG 85%) -> Tự động upload lên WordPress Media Library qua REST API.
3. **Xuất Bản Bài Viết Lên WordPress (Auto Publish)**:
   * Gọi API `wp-json/pbn/v1/create-post` trên site con với bài viết, danh mục, tags và ảnh đại diện (Featured Image).

---

## 4. DANH SÁCH REST API CẦN TRIỂN KHAI TRÊN FASTAPI V2

| Phương thức | Đường dẫn Endpoint | Mô tả |
| :--- | :--- | :--- |
| **POST** | `/api/auth/login` | Đăng nhập tài khoản quản trị, nhận JWT 7 ngày |
| **GET** | `/api/auth/me` | Xác thực token hiện tại, lấy thông tin user |
| **GET** | `/api/stats` | Thống kê tổng số site, online/offline, máy chủ, link |
| **GET** | `/api/sites` | Lấy danh sách site đã duyệt (hỗ trợ phân trang, lọc) |
| **GET** | `/api/sites/pending` | Lấy danh sách site chờ phê duyệt |
| **POST** | `/api/sites/approve` | Phê duyệt site (đơn lẻ hoặc hàng loạt) |
| **POST** | `/api/sites/reject` | Từ chối / xóa site (đơn lẻ hoặc hàng loạt) |
| **POST** | `/api/sites/ping` | Nhận heartbeat ping từ WordPress site |
| **GET** | `/api/servers` | Lấy danh sách máy chủ VPS / cPanel |
| **POST** | `/api/servers` | Thêm máy chủ mới |
| **PUT** | `/api/servers/{id}` | Cập nhật thông tin máy chủ |
| **DELETE**| `/api/servers/{id}` | Xóa máy chủ |
| **POST** | `/api/servers/{id}/test` | Kiểm tra kết nối SSH / API máy chủ |
| **POST** | `/api/servers/{id}/scan` | Quét tất cả WP site trên máy chủ |
| **POST** | `/api/servers/{id}/deploy`| Cài mu-plugin lên tất cả WP site của máy chủ |
| **POST** | `/api/servers/scan-all` | Quét toàn bộ các máy chủ trong hệ thống |
| **POST** | `/api/servers/deploy-all`| Cài mu-plugin lên toàn bộ các máy chủ |
| **GET** | `/api/backlinks` | Lấy danh sách backlink |
| **POST** | `/api/backlinks` | Chèn backlink mới |
| **POST** | `/api/backlinks/verify`| Kiểm tra trạng thái sống/chết của backlink |
| **DELETE**| `/api/backlinks/{id}` | Xóa backlink |
| **GET** | `/api/posts` | Lấy danh sách bài viết đã đăng |
| **GET** | `/api/log` | Lấy nhật ký hoạt động hệ thống |
| **GET** | `/api/settings` | Lấy cấu hình AI và hệ thống |
| **POST** | `/api/settings` | Cập nhật cấu hình |
| **WS** | `/ws` | Kênh WebSocket realtime gửi sự kiện lên giao diện |

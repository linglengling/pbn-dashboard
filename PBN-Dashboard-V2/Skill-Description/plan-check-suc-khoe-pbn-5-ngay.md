# Kế Hoạch Kiểm Tra Sức Khỏe Toàn Bộ Hệ Thống PBN Định Kỳ (5 Ngày / Lần — Giờ Khuya)

> **Mục tiêu:** Tự động kiểm tra toàn bộ hơn 1.050–1.200+ website PBN đang vận hành trên **11 server** (8 VPS aaPanel + 3 cPanel CloudLinux) theo chu kỳ **5 ngày thực 1 lần** vào **khung giờ khuya**, **chạy tự động 24/7 trên Server Master (`103.106.105.77`)** (không phụ thuộc máy tính cá nhân bật hay tắt), **đồng bộ toàn bộ kết quả lên tool Dashboard (`https://pbn.keodinh.net/audit`)** và gửi **1 báo cáo tổng hợp tiếng Việt** qua AI.
>
> **Nguyên tắc cố định:** **Chỉ kiểm tra, cập nhật lên tool `/audit` và báo cáo (Read-Only trên từng site & VPS vệ tinh)** — không tự ý sửa DB WordPress, không mở index hay xóa bài tự động; chủ hệ thống xem báo cáo xong sẽ chỉ định sửa từng site cụ thể sau.

---

## 1. Kiến Trúc Kết Hợp: Server 24/7 + AI Review (`Hybrid 24/7`)

| Thành phần | Thời điểm chạy | Nhiệm vụ | Đầu ra & Đồng bộ |
| :--- | :--- | :--- | :--- |
| **1. Server Master (`103.106.105.77`)**<br>Script `pbn_deep_audit.py --auto-schedule` | `01:00` giờ Việt Nam<br>(`22:00` giờ Dubai tối hôm trước)<br>*(Crontab `0 18 * * *` UTC, cổng 5 ngày thực `today_vn >= next_due_date`, bắt đầu `2026-11-26`)* | Chạy **24/7 độc lập** dù máy tính cá nhân tắt: quét 4 lớp toàn bộ **11 server** + toàn bộ domain trong `pbn_matrix.db`, đồng thời gọi AI nội bộ (`9router-1` tại `127.0.0.1:20128`) phân loại bài mới/nghi vấn | • Đồng bộ trực tiếp vào `pbn_matrix.db` (`site_audits`, `sites`, `LAST_AUDIT_REPORT`, `LAST_AUDIT_RUN`)<br>• Tạo `audit_reports/latest_ai_packet.json` (`ai_reviewed: false`) & cập nhật `next_due_date = today + 5 ngày` |
| **2. OpenMausBot (AI Review & Báo cáo)**<br>Automation `PBN Tổng hợp Report...` | `05:00` giờ Việt Nam<br>(`02:00` giờ Dubai)<br>*(Lịch `0 5 */5 * *` giờ VN)* | Đọc `latest_ai_packet.json` từ `103.106.105.77`, rà soát sâu bài mới/mu-plugin/outlink mới/lỗi bất thường, đồng bộ bổ sung nếu cần và đánh dấu `ai_reviewed: true` | • Lưu `reports/pbn_report_<YYYY-MM-DD>.md`<br>• Gửi bản báo cáo tiếng Việt ngắn gọn vào khung chat |

> **Xử lý khi máy tính cá nhân tắt:** Toàn bộ quá trình quét 11 server, gọi 9Router AI và cập nhật `https://pbn.keodinh.net/audit` đã chạy hoàn tất 24/7 ngay trên `103.106.105.77`. Đêm không mở máy tính chỉ bỏ qua bước tóm tắt chat lúc `05:00` VN — dữ liệu trên `/audit` và gói `latest_ai_packet.json` vẫn nguyên vẹn để AI đọc lại bất kỳ lúc nào.

---

## 2. Danh Sách 11 Server Mục Tiêu

- **8 VPS aaPanel:**
  1. `VPS aaPanel Master` (`103.106.105.77`)
  2. `VPS aaPanel 1` (`194.233.83.83`)
  3. `VPS aaPanel 2` (`172.96.190.231`)
  4. `VPS aaPanel 3` (`198.252.110.104`)
  5. `VPS aaPanel 4` (`198.252.101.160`)
  6. `VPS aaPanel 5` (`198.252.99.79`)
  7. `VPS aaPanel 6` (`172.96.184.18`)
  8. `VPS aaPanel 7` (`154.26.129.207`)
- **3 cPanel CloudLinux:**
  9. `cPanel SNG-SD120` (`sng-sd120.arandomserver.com`)
  10. `cPanel DAL-SD201` (`dal-sd201.arandomserver.com`)
  11. `cPanel TOR-SD204` (`tor-sd204.arandomserver.com`)

---

## 3. Quy Trình Kiểm Tra 4 Lớp (Read-Only)

### Lớp 1: Hạ tầng Server & Dịch vụ (MySQL / Web Server / Ổ đĩa)
- Kiểm tra trên **8 VPS aaPanel**:
  - Trạng thái dịch vụ **MySQL / MariaDB** (`mariadb` / `mysqld` đang active hay bị tắt/treo).
  - Trạng thái **Web Server** (`lshttpd` / `nginx` / `httpd`).
  - Dung lượng ổ đĩa trống `/` (cảnh báo nếu dùng >= 85%).
- Kiểm tra kết nối DB của từng site WordPress trên cả 11 server (đọc thông tin DB từ `wp-config.php` và test query `SELECT 1` qua PHP `mysqli` read-only).

### Lớp 2: Kết nối Mạng, Truy cập Live & Lỗi WordPress
- Kiểm tra phân giải DNS (`DNS_ERROR`, `DNS_LOOPBACK`).
- Gửi HTTP/HTTPS request từ bên ngoài:
  - **Không truy cập được:** Cloudflare `520–524` (`CLOUDFLARE_ERROR`), `CONN_ERROR` (timeout, connection refused, lỗi SSL), `HTTP_403`, `HTTP_404`, `HTTP_5xx`.
  - **Lỗi DB / PHP / Trang trắng / Parking:** `DB_ERROR`, `PHP_FATAL`, `BLANK_PAGE`, `PARKING_PAGE`.
  - **Redirect bất thường:** Phát hiện chuyển hướng `301/302` trỏ ra domain lạ ngoài danh sách `redirect_to` đã cấu hình trong `pbn_matrix.db` → mã `REDIRECT_STRANGE`.

### Lớp 3: Kiểm tra Google Index (NoIndex)
- **Từ giao diện live:** thẻ `<meta name="robots" content="*noindex*">`, header `X-Robots-Tag: noindex`, `/robots.txt` chứa `Disallow: /`.
- **Từ WordPress DB & mã nguồn (qua SSH):** `wp_options.blog_public = 0` hoặc file `robots.txt` vật lý `Disallow: /`.
- Site hoạt động tốt nhưng chặn index: đặt `is_noindex = 1`, `error_type = 'NOINDEX'`.

### Lớp 4: Phát hiện Bài Viết Lạ, Admin Lạ & Mã Độc
- **Bài viết / Trang bất thường (last 6 days):**
  - Liệt kê các bài `post_status = 'publish'` (`post` / `page`) mới đăng hoặc mới sửa trong 6 ngày gần nhất; kiểm tra tác giả lạ, thẻ `<script>`, `<iframe>`, CSS ẩn, và phân tích ngữ nghĩa qua **9Router AI (`9router-1`)** → gắn cờ `WP_SUSPECT_POST` nếu phát hiện spam ngoại lai.
  - Theo dõi **Outbound Links** mới phát sinh trên trang chủ so với `audit_reports/outbound_baseline.json`.
- **Tài khoản Admin lạ (`WP_STRANGE_ADMIN`):** kiểm tra `wp_users` quyền `administrator` ngoài whitelist (`klao`, `ad_official`, `owen`, `piel`, `yura`, `admin`).
- **Mã độc ngoại lai (`MALWARE_DETECTED`, tuân thủ Whitelist chủ hệ thống):**
  - Quét `flux-wrapper-dex`, `SC_TH_BEGIN` trong `functions.php`, `SCOCV:` / `.wp-object-cache-` trong `object-cache.php` / `advanced-cache.php`, thư mục `.sc_*` / `.gk_*`, file `[0-9a-f]{8}.zip` và liệt kê `mu-plugins/*.php` ngoài whitelist.
  - **Tuyệt đối giữ nguyên (Whitelist):** user `klao`, `ad_official`, `owen`, `piel`, `yura`, `admin`; `wp-content/mu-plugins/init.php`, `wp-seo-rank-math.php`, `p-manager.php`, `p-manager-u.php`, `restrict-plugin-activation.php`, `force-plugins.php`.

---

## 4. Lệnh Chạy & Kiểm Thử Thủ Công

```bash
# Kiểm thử an toàn trên 1-2 server (Read-Only, không sửa DB production hay lịch)
python3 /www/wwwroot/pbn-management2.keodinh.net/pbn_deep_audit.py --dry-run-server 35,2

# Chạy tự động theo cổng 5 ngày thực (crontab 01:00 VN)
python3 /www/wwwroot/pbn-management2.keodinh.net/pbn_deep_audit.py --auto-schedule

# Chạy cưỡng bức toàn bộ 11 server ngay lập tức (khi cần đối soát đột xuất)
python3 /www/wwwroot/pbn-management2.keodinh.net/pbn_deep_audit.py --force
```

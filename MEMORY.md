# Shared Operational Memory (`MEMORY.md`)

> **Mục đích:** Bộ nhớ dùng chung giữa các agent / máy tính (Antigravity, Hermes, OpenClaw...) qua Git (`https://github.com/linglengling/pbn-dashboard.git`).
> - Kiến trúc hệ thống & thông tin server tĩnh xem tại `AI-handover.md`.
> - Tài liệu skill & plan tiếng Việt lưu tại `PBN-Dashboard-V2/Skill-Description/`.
> - **Quy tắc:** Luôn `git pull` trước khi làm việc và `git push` sau khi cập nhật code / plan / skill / memory. Không lưu token/mật khẩu mới hay file `*.db` vào Git.

---

## 1. Quy Ước Kỹ Thuật Dùng Chung Mới Nhất
- **`mu-plugins/init.php` (Canonical Source):**
  - Đã xóa toàn bộ comment giải thích và mã hóa Base64 (`eval(base64_decode($c))`), lưu trực tiếp tại `mu-plugins/init.php` (MD5 `67a9bb65f633a08fa4f5514a8d93818b`, 167,049 bytes).
  - **KHÔNG tải từ CDN** (`http://cdn.keodinh.net/wp/mu-plugins.zip?dd=44` hay `mu-plugins.tar.gz`) nữa — tất cả script cài site (`13-cai-plugin-sites.py`, `update-nwm-khoa-file-*.py`) và skill `pbn-site-provision` đều lấy trực tiếp từ `mu-plugins/init.php`.
  - Đã deploy đồng bộ lên **1,221/1,221 site** trên cả 11 server (8 VPS + 3 cPanel) và đồng bộ lên `103.106.105.77` (`/root/mu-plugins-src/mu-plugins/init.php` & `/www/wwwroot/pbn-management2.keodinh.net/mu-plugins/init.php`).
- **Dual Manager Rule (`p-manager.php` vs `p-manager-u.php`):**
  - VPS aaPanel: dùng `mu-plugins/p-manager.php` (Base64).
  - cPanel CloudLinux: dùng `mu-plugins/p-manager-u.php` (Plain PHP ẩn danh) và xóa `p-manager.php`.
- **Site Audit (`PBN-Dashboard-V2`):**
  - Tab `/audit` mặc định lọc `ISSUES` (`Site Lỗi & Chặn Index`), tách riêng site khỏe (`SEO OK`).
  - `AuditTab.jsx` xử lý HTTP `401` (tự xóa `pbn_token` hết hạn & reload đăng nhập) và hiển thị chi tiết lỗi Mở Index.
  - Server `103.106.105.77` chạy tự động quét 3 ngày/lần qua `_audit_cron_daemon()` + OS crontab `0 3 */3 * *`. *(Không cài cron trên máy local Windows trừ khi chủ hệ thống yêu cầu).*
- **Shared Bot Workspace trên Server `103.106.105.77` (`/www/wwwroot/phn-manage.sites/src-github`):**
  - Thư mục này là workspace chung dành cho nhiều AI Bot (Hermes Agent, OpenClaw, Antigravity...) cùng truy cập và xử lý trực tiếp trên VPS.
  - Đã cấu hình Git (`linglengling/pbn-dashboard`), `git_sync_config.json`, và `safe.directory`.
  - **Quy tắc bắt buộc:** Mỗi lần đẩy/deploy bất kỳ thứ gì lên server hoặc hoàn tất push Git từ local, luôn phải pull tại thư mục này (`python scripts/git_sync.py pull-server` hoặc gọi tự động qua `scripts/git_sync.py push`) để workspace trên server luôn đồng bộ tức thì.

---

## 2. Việc Đang Chờ / Cần Theo Dõi (Pending)
- **Cloudflare Nameserver đang `pending` (chờ trỏ ở nhà đăng ký tên miền):**
  - `worldgiftednesscenter.org`, `thaiteqball.org`, `ijsra.org` (đã cài xong WP trên `103.106.105.77`, tài khoản `ad_official`, `piel`, `yura`, DNS A → `103.106.105.77` SSL Flexible): chờ trỏ NS về `annabel.ns.cloudflare.com` & `gerald.ns.cloudflare.com`.
  - `vb888.love` (đã cài trên `172.96.184.18`): chờ đổi NS về `grant.ns.cloudflare.com` & `jen.ns.cloudflare.com`.
- **Domain lỗi DNS cần kiểm tra:** `hitclubx.app` (chưa thấy zone trong 2 tài khoản CF; folder WP trên VPS 6 & VPS 8 đã có sẵn gói `vi`).
- **Plan đang chờ duyệt triển khai:**
  - `PBN-Dashboard-V2/Skill-Description/plan-bio-backlink-entity.md` (Bio Backlink Entity tự động trên PBN — chờ chủ hệ thống duyệt & bổ sung ý tưởng).
- **VPS 1 (`198.252.110.104`) — Dọn dự phòng sau phục hồi MariaDB (`2026-11-22`):**
  - Đã phục hồi sạch MariaDB 10.11.10 (`102` DBs, `tk2.keodinh.net` Matomo 284 sites / 521k+ visits hoạt động bình thường, trống `56G`).
  - Thư mục dự phòng `/www/server/data_corrupted_20261122`, `/www/backup/innodb_crash_bak_20261122`, `/www/backup/full_recovery_20261122` đang giữ tạm; sau 1–2 ngày ổn định có thể xóa để giải phóng thêm ~40+ GB.

---

## 3. Nhật Ký Ngắn Các Mốc Gần Nhất
- **2026-11-23:** Cài đặt hoàn tất OpenMausbot (`mausbot` trên PM2, port `8799`) tại `https://team.kiencanh.com`, OpenLiteSpeed reverse proxy (hỗ trợ WebSocket), tự động tạo bản ghi DNS Cloudflare A (Proxied) và cấp chứng chỉ SSL. Đã cấp quyền admin cho email `vnae88888886@gmail.com` tại `/pair`. Đã cấu hình và kết nối thành công Hermes Agent với 9Router AI Gateway nội bộ (`http://127.0.0.1:20128/v1`, model `9router-1`, 256k context); test phản hồi thành công và restart PM2 `hermes-web` + `mausbot`.
- **2026-11-22:** Thiết lập và đồng bộ workspace dùng chung cho AI Bot tại `/www/wwwroot/phn-manage.sites/src-github` trên VPS `103.106.105.77`; tích hợp tính năng tự động `pull_server()` vào `scripts/git_sync.py`.
- **2026-11-22:** Thiết lập `git_sync_config.json` (bảo vệ qua `.gitignore`), xây dựng tiện ích `scripts/git_sync.py`, tạo skill `pbn-git-sync` và tài liệu `huong-dan-dong-bo-git-memory.md` chuẩn hóa tự động pull trước / push sau khi thao tác code, plan, memory.
- **2026-11-22:** Phục hồi MariaDB VPS 1 (`198.252.110.104`) & khôi phục `tk2.keodinh.net`; cài mới 3 site WP (`worldgiftednesscenter.org`, `thaiteqball.org`, `ijsra.org`) trên `103.106.105.77`; chuyển remote Git sang `linglengling/pbn-dashboard` và loại `*.db` khỏi Git.
- **2026-11-21:** Xóa comment + mã hóa Base64 `mu-plugins/init.php`, deploy toàn bộ 1,221 site trên 11 server, bỏ link CDN `mu-plugins.zip`.
- **2026-11-19:** Sửa Site Audit (`ISSUES` default filter + 401 handling); kiểm tra & kích hoạt tiếng Việt (`vi`) cho 12 site Hitclub (11/11 live `lang="vi"`, sửa `hitclub6.eu.com`/`new.royalresidency.in` & flush cache `gamehitclub.it.com`/`v.viennaphoto.at`); hướng dẫn gắn 9Router (`103.106.105.77:20128`) vào Hermes Agent Web UI.

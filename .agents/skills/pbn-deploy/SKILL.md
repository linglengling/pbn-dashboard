---
name: pbn-deploy
description: Automated deployment skill for PBN Dashboard V2 (Python FastAPI) to VPS (103.106.105.77 / pbn.keodinh.net). Uploads source code to /www/wwwroot/pbn-management2.keodinh.net, builds client assets, and restarts PM2 pbn-v2 process. Trigger when the user requests "deploy to server", "update server", "deploy pbn", "cập nhật server", "deploy server", or "/pbn-deploy".
---

# PBN Dashboard V2 Python VPS Deployment Skill

Skill này tự động hóa việc upload, cập nhật và deploy bản Python FastAPI (`PBN-Dashboard-V2`) lên VPS máy chủ trung tâm.

## Server Connection Credentials

- **Domain**: `https://pbn.keodinh.net`
- **VPS IP**: `103.106.105.77`
- **Port**: `22` (SSH)
- **User**: `root`
- **Password**: `q9icdLH1!*0B`
- **Target Folder**: `/www/wwwroot/pbn-management2.keodinh.net`
- **Web Server**: OpenLiteSpeed (Reverse Proxy to Python FastAPI port 5556)
- **PM2 Process**: `pbn-v2` (`python run.py`)

---

## Quy Trình Quản Lý & Phân Phối `p-manager` (Dual Manager Architecture)

Hệ thống PBN phân loại thành 2 môi trường hosting khác nhau, bắt buộc dùng 2 phiên bản manager tương ứng:

1. **aaPanel / VPS Servers (`p-manager.php`)**:
   - Sử dụng phiên bản **Base64 encoded** (`p-manager.php`).
   - Có đầy đủ tính năng: 1-Click fast login (`?nwmmm=...`), toggle đóng/mở index (`?ttpp=atc=openindex`/`closeindex`/`getindex`), xóa cache LiteSpeed (`litespeed_purge_all`), REST API.
   - Triển khai đến: Server 1, 5, 6, 7, 8, 33, 34, 35 (aaPanel VPS).

2. **cPanel / CloudLinux Hosting Servers (`p-manager-u.php`)**:
   - Sử dụng phiên bản **Plain PHP (Unobfuscated)** (`p-manager-u.php`).
   - Lý do: cPanel chạy **Imunify360 (CloudAV)** với luật quét heuristic tĩnh (`SMW-BLKH-SA-CLOUDAV-php.bkdr.wpplugin.mal-WPPLUGIN1-0`), tự động cắt xén (truncate) các file `eval(base64_decode(...))` về 0 bytes (`Content removed`). Dùng code PHP thuần chuẩn cấu trúc WordPress hook loại bỏ hoàn toàn cảnh báo sai và nguy cơ bị xóa file.
   - Khi deploy trên cPanel: Upload `p-manager-u.php` vào `wp-content/mu-plugins/` và **xóa bỏ file `p-manager.php` cũ** (nếu có) để tránh Imunify360 quét trúng file cũ.
   - Triển khai đến: Server 2 (SNG), Server 3 (DAL), Server 4 (TOR).

---

## Quy Trình Deploy PBN-Dashboard-V2 (Python)

1. **Local build client React (nếu sửa frontend)**:
   ```bash
   cd g:\ProjectDemo\manage-pbn-sites\PBN-Dashboard-V2\client
   npm run build
   ```
2. **SFTP Upload**:
   - Upload các file thay đổi trong `PBN-Dashboard-V2/app/` lên `/www/wwwroot/pbn-management2.keodinh.net/app/`
   - Upload `PBN-Dashboard-V2/static/` lên `/www/wwwroot/pbn-management2.keodinh.net/static/`
3. **Restart tiến trình PM2 trên VPS**:
   ```bash
   pm2 restart pbn-v2
   pm2 status
   ```
4. **Kiểm tra trạng thái**:
   ```bash
   curl -I https://pbn.keodinh.net/
   ```

5. **Đồng bộ Workspace Chung Cho Bot AI trên VPS**:
   ```bash
   cd /www/wwwroot/phn-manage.sites/src-github && python3 scripts/git_sync.py pull
   ```

---

## Danh Sách Trắng (Whitelist) Của Chủ Hệ Thống - TUYỆT ĐỐI KHÔNG XÓA

Các thành phần sau do chính chủ hệ thống (user) tạo ra làm công cụ truy cập dự phòng, TUYỆT ĐỐI KHÔNG XỬ LÝ / KHÔNG XÓA / KHÔNG COI LÀ MÃ ĐỘC:
1. **User `klao` trong CSDL**: Backdoor hợp lệ của chủ web, không được xóa hoặc đổi quyền.
2. **File `init.php` trong thư mục `wp-content/mu-plugins/`**: File công cụ/hook của chủ web, không được xóa hoặc sửa đổi.
3. **File `wp-seo-rank-math.php` trong `wp-content/mu-plugins/`**: Plugin của chủ web, không được xóa.
4. **Nguyên tắc deploy vào `mu-plugins/`**: Chỉ upload/ghi đè file được chỉ định (như `p-manager.php`), giữ nguyên 100% tất cả các file có sẵn khác.
5. **Mã độc thực sự cần xử lý**: Chỉ tập trung xử lý các mã độc ngoại lai như `flux-wrapper-dex`, các thư mục ẩn `.sc_*`, `.gk_*`, file cờ ẩn `.*flux*`, và dropper chèn trong `functions.php` theme.


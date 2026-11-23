# Kế Hoạch & Phương Án Triển Khai Mausbot (OpenMausbot) Trên Server aaPanel (103.106.105.77)

> **Mục tiêu:** Cài đặt hệ thống **Mausbot** (OpenMausbot / OMB) chạy nền 24/7 bằng Docker trên Central VPS `103.106.105.77`, kết nối đồng bộ hai chiều (2-way sync) với ứng dụng máy tính (Desktop Client) và điện thoại mà **tuyệt đối không gây xung đột** với web server OpenLiteSpeed, PBN Dashboard V2, hay các website WordPress đang chạy.

---

## 1. Phân Tích Kỹ Thuật & Kiến Trúc Hệ Thống

### 1.1. Bản Chất Của Mausbot (OpenMausbot)
- **Cơ chế hoạt động:** Mausbot là một nền tảng agentic harness chạy container, cho phép quản lý các AI workspace độc lập trên server.
- **Tính năng đồng bộ (Make Home):** Sau khi kết nối (pair) giữa Desktop App và Server, tính năng "Make this my home" sẽ tự động sync toàn bộ memory, cấu hình, và dàn agent từ máy local sang VPS, cho phép bot tự động chạy ngầm liên tục kể cả khi tắt máy tính.
- **Ghép nối (Pairing):** Hỗ trợ ghép nối qua OTP Email (`/pair`) hoặc qua mã 12 ký tự / QR Code được sinh bằng lệnh CLI `openmausbot pair`.

### 1.2. So Sánh Thực Tế: Hướng Dẫn Facebook (Dokploy + Caddy) vs. Hệ Thống Hiện Tại (aaPanel + OpenLiteSpeed)
Trong bài viết mẫu hướng dẫn trên Facebook:
- Sử dụng **Dokploy** (Web UI quản lý Docker container).
- Chạy 2 container: `omb` (core backend) và `caddy` (reverse proxy kiêm tự cấp SSL Let's Encrypt trên port 80 và 443).

**Điểm xung đột cốt lõi trên server 103.106.105.77:**
1. **Xung đột Port 80 và 443:** Trên VPS `103.106.105.77`, OpenLiteSpeed (`lsws`) đang lắng nghe trực tiếp trên cổng 80 và 443 để phục vụ `pbn.keodinh.net` và các vhost WordPress. Nếu chạy container Caddy chiếm cổng 80/443, Docker sẽ báo lỗi `bind: address already in use` hoặc làm gián đoạn toàn bộ website đang chạy.
2. **Không cần cài Dokploy:** Server đã có aaPanel quản lý toàn diện và Docker Engine cài sẵn. Cài thêm Dokploy sẽ làm nặng VPS và gây dư thừa tài nguyên.

---

## 2. Các Phương Án Triển Khai

| Tiêu chí | Phương án 1 (Khuyên dùng - Native aaPanel) | Phương án 2 (Chạy Caddy qua Port phụ) |
| :--- | :--- | :--- |
| **Kiến trúc** | Chạy duy nhất container `omb`, OpenLiteSpeed làm Reverse Proxy | Giữ nguyên cụm `omb` + `caddy`, map Caddy ra port phụ (vd: `8443`) |
| **Mức độ an toàn** | **Tuyệt đối an toàn 100%**, không đụng chạm port 80/443 | An toàn nhưng phải mở thêm port firewall |
| **Trải nghiệm truy cập** | Chuẩn tên miền HTTPS đẹp (vd: `https://maus.keodinh.net`) | Phải kèm port (vd: `https://maus.keodinh.net:8443`) |
| **Tiêu tốn tài nguyên** | Tiết kiệm RAM/CPU (không cần chạy thêm Caddy) | Thừa 1 container Caddy không cần thiết |
| **Độ ổn định** | Tận dụng sẵn OpenLiteSpeed & Cloudflare SSL | Caddy cần tự quản lý chứng chỉ SSL riêng |

👉 **Đề xuất lựa chọn: Phương án 1 (Native aaPanel Reverse Proxy)**.

---

## 3. Chi Tiết Kỹ Thuật Triển Khai (Phương Án 1)

### Bước 1: Chuẩn Bị Tên Miền / Subdomain & DNS
- Chọn một subdomain đại diện, ví dụ: `maus.keodinh.net` (hoặc tên miền riêng do bạn chỉ định).
- Trỏ bản ghi DNS trên Cloudflare:
  - **Type:** `A`
  - **Name:** `maus` (hoặc tên tuỳ chọn)
  - **IPv4 Address:** `103.106.105.77`
  - **Proxy status:** Bật `Proxied` (đám mây cam) để được bảo vệ DDoS và có SSL Cloudflare tự động.

### Bước 2: Tạo Docker Compose Cho Core Service `omb`
Khởi tạo thư mục làm việc tại VPS: `/www/server/mausbot` (hoặc `/opt/openmausbot`).
File `docker-compose.yml` tối ưu cho aaPanel:

```yaml
version: '3.8'

services:
  omb:
    image: ghcr.io/milind-soni/openmausbot:latest
    container_name: mausbot-omb
    restart: unless-stopped
    init: true
    shm_size: 512m
    environment:
      - OMB_PORT=8799
      - OMB_SERVER_NAME=${OMB_SERVER_NAME:-mausbot-prod}
      - OMB_PUBLIC_URL=https://${DOMAIN}
      - OMB_SIGNIN_EMAILS=${OMB_SIGNIN_EMAILS}
      # Tích hợp sẵn 9Router AI Gateway nội bộ nếu muốn:
      # - OPENAI_BASE_URL=http://172.17.0.1:20128/v1
    ports:
      # Chỉ bind nội bộ localhost, không mở public port này ra internet
      - "127.0.0.1:8799:8799"
    volumes:
      - ./data:/data
    logging:
      driver: "json-file"
      options:
        max-size: "20m"
        max-file: "3"
```

File `.env` đi kèm:
```env
DOMAIN=maus.keodinh.net
OMB_SERVER_NAME=Mausbot-Keodinh
OMB_SIGNIN_EMAILS=admin@your-email.com
```

### Bước 3: Cấu Hình Website & Reverse Proxy Trên aaPanel (OpenLiteSpeed)
1. Trong aaPanel → Mục **Website** → Thêm site mới với domain: `maus.keodinh.net`.
2. Mở cấu hình site vừa tạo → Tab **Reverse Proxy** → Thêm Reverse Proxy:
   - **Proxy Name:** `mausbot_proxy`
   - **Target URL:** `http://127.0.0.1:8799`
   - **Sent Domain:** `$host`
3. Cấu hình hỗ trợ **WebSocket** (cực kỳ quan trọng để app Desktop / Mobile đồng bộ realtime):
   ```apache
   RewriteEngine On
   RewriteCond %{HTTP:Upgrade} =websocket [NC]
   RewriteRule /(.*) ws://127.0.0.1:8799/$1 [P,L]
   RewriteCond %{HTTP:Upgrade} !=websocket [NC]
   RewriteRule /(.*) http://127.0.0.1:8799/$1 [P,L]
   ```
4. Bật SSL trong tab **SSL** (dùng Let's Encrypt hoặc Cloudflare Origin Certificate).

### Bước 4: Khởi Động Container & Ghép Nối (Pairing)
1. Chạy container:
   ```bash
   cd /www/server/mausbot && docker compose up -d
   ```
2. Kiểm tra container hoạt động:
   ```bash
   docker ps | grep mausbot
   curl -I http://127.0.0.1:8799/api/health
   ```
3. Lấy mã Pairing để kết nối với Máy tính / Điện thoại:
   - **Cách 1 (Email OTP):** Vào thẳng trình duyệt `https://maus.keodinh.net/pair`, nhập email đã đăng ký ở `OMB_SIGNIN_EMAILS` để nhận mã xác thực một lần.
   - **Cách 2 (Mã Pairing 12 ký tự / QR Code):** Chạy lệnh trong terminal:
     ```bash
     docker exec -it mausbot-omb openmausbot pair
     ```
     Màn hình sẽ hiển thị mã 12 ký tự và link dạng:
     `https://maus.keodinh.net/pair#code=XXXX-XXXX-XXXX`
4. Mở ứng dụng **MausBot Desktop** trên máy tính:
   - Nhấn dấu `＋` → Chọn **Connect to a server**.
   - Dán URL pairing vào.
   - Sau khi kết nối thành công: Click chuột trái vào workspace server → Chọn **"Make this my home"** để đẩy toàn bộ bot và memory từ máy local lên VPS.

---

## 4. Các Thông Tin Cần Xác Nhận Trước Khi Thực Hiện

Để tiến hành cài đặt chính xác ngay, bạn vui lòng cho biết:
1. **Tên miền / Subdomain** bạn muốn dùng cho Mausbot: (ví dụ `maus.keodinh.net` hay một tên miền nào khác?).
2. **Email quản trị viên** bạn muốn cấu hình để nhận mã đăng nhập OTP (`OMB_SIGNIN_EMAILS`).
3. Bạn có muốn cấu hình kết nối trực tiếp với **9Router AI Gateway** (`port 20128`) đang có sẵn trên VPS này để cấp LLM miễn phí cho bot không?

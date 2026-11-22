---
name: pbn-backlink
description: Quy chuẩn và quy trình tự động đi backlink cho hệ thống PBN (chèn menu header, đi backlink chéo nội bộ network, và rải backlink cho 5 Brand cá cược/casino vào bài viết trang chủ kèm kiểm tra/thay thế link chết). Kích hoạt khi user yêu cầu "đi backlink", "chèn backlink", "thay backlink", "pbn-backlink", hoặc gửi bảng yêu cầu đi link.
---

# PBN Backlink Injection & Network Link Building Skill

Skill này định nghĩa toàn bộ quy chuẩn, logic thuật toán và các bước kiểm tra (QA) khi thực hiện chiến dịch đi backlink trên mạng lưới vệ tinh PBN WordPress.

---

## 0. QUY TẮC BẮT BUỘC: BACKUP DATABASE TRƯỚC MỌI THAO TÁC
> [!CAUTION]
> **TRƯỚC KHI LÀM BẤT CỨ ĐIỀU GÌ** (sửa database, chèn bài viết, đi backlink, sửa code hay cài plugin):
> **BẮT BUỘC** phải tạo bản backup Database (Full DB hoặc bảng `wp_posts`, `wp_postmeta`, `wp_options` liên quan) trước tiên.

1. **Lệnh Backup bắt buộc**:
   Tạo thư mục backup có timestamp rõ ràng:
   ```bash
   mkdir -p /www/backup/pbn_backups_before_change
   mysqldump -u root -p'dc2fe6f2608cdc00' {db_name} | gzip > /www/backup/pbn_backups_before_change/{domain}_{timestamp}.sql.gz
   ```
2. **Nguyên tắc an toàn DB**:
   - Tuyệt đối không dùng lệnh dump có cờ `--where` rồi restore đè trực tiếp vì mysqldump sẽ sinh `DROP TABLE IF EXISTS wp_posts;` làm mất toàn bộ bài viết khác.
   - Thao tác sửa nội dung phải dùng câu lệnh cập nhật có tham số (parameterized query) thông qua PyMySQL hoặc WP-CLI, không can thiệp bằng regex thô trong bash script.
3. **Quy tắc về Menu:** Trừ khi có yêu cầu cụ thể bằng văn bản, **KHÔNG ĐƯỢC PHÉP can thiệp vào menu header/navigation** của website khi chỉ được giao nhiệm vụ đi backlink trang chủ. Giữ nguyên 100% menu điều hướng gốc.
4. **Quy tắc về Gutenberg & Ký tự lạ:**
   - Toàn bộ nội dung chèn mới phải được bọc trong block Gutenberg HTML chuẩn: `<!-- wp:html --> ... <!-- /wp:html -->`.
   - Tuyệt đối không để rò rỉ ký tự literal `\n` vào nội dung bài viết.
   - Sau khi cập nhật, bắt buộc phải xóa sạch cache (W3 Total Cache và LiteSpeed Cache) và reload LiteSpeed web server.
5. **Quy tắc Whitelist Chủ Hệ Thống**: Tuyệt đối không xóa hay can thiệp vào user `klao` trong DB, file `wp-content/mu-plugins/init.php` và `wp-content/mu-plugins/wp-seo-rank-math.php` vì đây là các công cụ do chính chủ hệ thống tạo ra.

---

## 1. Bản Đồ 24 Website Vệ Tinh (Network Sites)
Tất cả 24 site nằm trên máy chủ trung tâm (`103.106.105.77`), docroot `/www/wwwroot/<domain>`:

| STT | Domain Nguồn | Web Server / Server ID | DB Target |
|:---:|:---|:---:|:---|
| 1 | `aaidudec.org` | 103.106.105.77 (Server 35) | Local MySQL |
| 2 | `anthonyruivivar.net` | 103.106.105.77 (Server 35) | Local MySQL |
| 3 | `bblatinamerica.com` | 103.106.105.77 (Server 35) | Local MySQL |
| 4 | `conadecivil.com` | 103.106.105.77 (Server 35) | Local MySQL |
| 5 | `facturatabasco.com` | 103.106.105.77 (Server 35) | Local MySQL |
| 6 | `greatdrivingchallenge.com` | 103.106.105.77 (Server 35) | Local MySQL |
| 7 | `hkhoe.com` | 103.106.105.77 (Server 35) | Local MySQL |
| 8 | `sburlrecdept.com` | 103.106.105.77 (Server 35) | Local MySQL |
| 9 | `shadowdance.org` | 103.106.105.77 (Server 35) | Local MySQL |
| 10 | `smvhighschool.in` | 103.106.105.77 (Server 35) | Local MySQL |
| 11 | `snow-design.com` | 103.106.105.77 (Server 35) | Local MySQL |
| 12 | `stepl.org` | 103.106.105.77 (Server 35) | Local MySQL |
| 13 | `suzanneloebl.com` | 103.106.105.77 (Server 35) | Local MySQL |
| 14 | `thaiasiatoday.com` | 103.106.105.77 (Server 35) | Local MySQL |
| 15 | `feshun.com` | 103.106.105.77 (Server 35) | Local MySQL |
| 16 | `hellbenderpress.com` | 103.106.105.77 (Server 35) | Local MySQL |
| 17 | `innkeeperrockies.com` | 103.106.105.77 (Server 35) | Local MySQL |
| 18 | `rogalevich.org` | 103.106.105.77 (Server 35) | Local MySQL |
| 19 | `j-core.biz` | 103.106.105.77 (Server 35) | Local MySQL |
| 20 | `kvdevelopers.com` | 103.106.105.77 (Server 35) | Local MySQL |
| 21 | `benscarpage.com` | 103.106.105.77 (Server 35) | Local MySQL |
| 22 | `kylehendersonmusic.com` | 103.106.105.77 (Server 35) | Local MySQL |
| 23 | `respectablyfrench.com` | 103.106.105.77 (Server 35) | Local MySQL |
| 24 | `sougicocoro.com` | 103.106.105.77 (Server 35) | Local MySQL |

---

## 2. Ba Trụ Cột Triển Khai Backlink

### Trụ Cột 1: Đi Link Chéo Nội Bộ Network (Cột C)
- **Công thức chọn đích**: Mỗi site thứ `i` (từ 1 đến 24) sẽ link tới 4 site tiếp theo bên dưới theo chu kỳ vòng tròn (circular shift):
  - Site 1 ➔ trỏ tới các site: `2, 3, 4, 5`
  - Site 2 ➔ trỏ tới các site: `3, 4, 5, 6`
  - Site 3 ➔ trỏ tới các site: `4, 5, 6, 7`
  - ...
  - Site 21 ➔ trỏ tới: `22, 23, 24, 1`
  - Site 22 ➔ trỏ tới: `23, 24, 1, 2`
  - Site 23 ➔ trỏ tới: `24, 1, 2, 3`
  - Site 24 ➔ trỏ tới: `1, 2, 3, 4`
- **Tỷ lệ Anchor Text**:
  - **50% Link trần (Naked URL)**: Dạng `https://domain.com` hoặc `domain.com`.
  - **50% Brand Keyword tự nhiên**: AI phân tích ngữ cảnh / thương hiệu gốc của site đích để chọn từ khóa phù hợp (ví dụ: `jilibet`, `1xbet`, `88app`, `FB777`, `KClub`, v.v.).
- **Vị trí đặt**: Lồng ghép tự nhiên vào bài viết hiển thị ở trang chủ (homepage posts).

---

### Trụ Cột 2: Chèn Link Vào Menu Header (Cột D & E)
Chèn 2 custom link vào menu chính (`nav_menu`) của WordPress theo quy luật hàng lẻ / hàng chẵn xen kẽ:

| Dòng STT | Cặp Link Menu Cần Chèn | Cấu Hình Link & Anchor Text |
|:---:|:---|:---|
| **Hàng Lẻ** (1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23) | **BU88** & **VB88** | 1. URL: `https://bu88.com` (Anchor: `BU88`)<br>2. URL: `https://vb88.com` (Anchor: `VB88`) |
| **Hàng Chẵn** (2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24) | **X8 Club** & **HD88** | 1. URL: `https://x8.club` (Anchor: `X8 Club`)<br>2. URL: `https://hd88.com` (Anchor: `HD88`) |

- **Thuộc tính link**: `target="_blank"`, `rel="noopener"`.

---

### Trụ Cột 3: Bổ Sung Backlink Cho 5 Brand Mục Tiêu (Cột Phải)
Bổ sung đoạn nội dung phù hợp vào bài viết trang chủ của toàn bộ 24 site, trỏ về **đủ 5 Brand** sau:

1. **Brand 1: `ivibet`**
   - Kho domain đích: `ivibetguia.com`, `ivibetreviews.com`
2. **Brand 2: `b2xbet`**
   - Kho domain đích: `b2xbetbonusbr.com`, `b2xbetguia.com`, `b2xbetreview.com`
3. **Brand 3: `megapari`**
   - Kho domain đích: `megaparibonusbr.com`, `megapariguia.com`
4. **Brand 4: `fresh casino`**
   - Kho domain đích: `freshcasinobonusbr.com`, `freshcasinoguia.com`
5. **Brand 5: `jet casino`**
   - Kho domain đích: `jetcasinobonusbr.com`, `jetcasinoguia.com`

- **Nguyên tắc phân bổ (Load Balancing)**:
  - Trên mỗi site, mỗi brand bốc chọn ngẫu nhiên **1 domain** từ danh sách của brand đó.
  - Xoay tua đều giữa các site sao cho tần suất xuất hiện giữa các domain trong cùng một brand là cân bằng nhất.

---

## 3. Quy Trình Kiểm Tra Link Chết (Dead Link Auditing & Replacement)
Trước khi chèn mới:
1. **Quét toàn bộ outbound links hiện có** trên trang chủ của 24 site.
2. **Kiểm tra DNS & HTTP status** của từng URL đích:
   - Nếu domain đích không phân giải được IP (DNS Dead), hoặc trả về HTTP 4xx, 5xx, hoặc hết hạn (như `1xbetph.org`):
   - Đánh dấu là **Link Chết (Dead Link)**.
3. **Thay thế**:
   - Gỡ bỏ link chết khỏi bài viết / menu.
   - Thay thế bằng domain mới tương ứng với anchor text và câu văn ngữ cảnh phù hợp theo yêu cầu của chiến dịch.

---

## 4. Tiêu Chuẩn Báo Cáo QA (Quality Assurance)
Sau khi thực thi, xuất bảng báo cáo QA chi tiết:
1. Danh sách link chết đã phát hiện & đã gỡ bỏ/thay thế trên từng site.
2. Danh sách link menu đã chèn (kiểm tra live HTTP 200).
3. Danh sách 4 link network nội bộ đã chèn (URL đích + Anchor text + Loại: Naked / Brand).
4. Danh sách 5 Brand link đã chèn (Brand + URL bốc chọn + Anchor text).
5. Trạng thái live test thực tế qua `curl` trên frontend của từng site.


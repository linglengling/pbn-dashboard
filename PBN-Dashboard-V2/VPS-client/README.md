# PBN VPS Client Tools (`/www/wwwroot/pbn-tool`)

Thư mục công cụ điều khiển cục bộ trên các máy chủ VPS aaPanel & Hosting.

### Cấu trúc thư mục:
- `auto_scan_sites.py`: Script tự động quét tất cả website WordPress trên máy chủ, tự động cài `p-manager.php` cho các website mới tạo và đồng bộ danh sách site về Dashboard trung tâm (`https://pbn.keodinh.net/api/vps/sync-sites`).
- `p-manager.php`: Bản mã hóa của plugin Must-Use để `auto_scan_sites.py` tự động nạp vào các site mới.
- `pbn_agent.py`: Agent Python tự động thu thập thông số (CPU, RAM, Disk, số lượng site) và gửi tín hiệu định kỳ về máy chủ Dashboard trung tâm (`https://pbn.keodinh.net/api/vps/signal`).
- `signal.php`: Script PHP kết nối tín hiệu dự phòng.

### Cấu hình Cron Job (3 ngày 1 lần vào lúc 03:00 sáng):
```bash
0 3 */3 * * /usr/bin/python3 /www/wwwroot/pbn-tool/auto_scan_sites.py >> /www/wwwroot/pbn-tool/cron_scan.log 2>&1
```

### Chạy thủ công kiểm tra ngay:
```bash
python3 /www/wwwroot/pbn-tool/auto_scan_sites.py
```

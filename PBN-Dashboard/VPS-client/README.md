# PBN VPS Client Tools (`/www/wwwroot/pbn-tool`)

Thư mục công cụ điều khiển cục bộ trên các máy chủ VPS aaPanel.

### Cấu trúc thư mục:
- `pbn_agent.py`: Agent Python tự động thu thập thông số (CPU, RAM, Disk, số lượng site) và gửi tín hiệu định kỳ về máy chủ Dashboard trung tâm (`https://pbn.keodinh.net/api/vps/signal`).
- `signal.php`: Script PHP kết nối tín hiệu dự phòng, có thể gọi trực tiếp bằng `php signal.php` hoặc qua Web.

### Hướng dẫn sử dụng:
1. Gửi tín hiệu 1 lần:
   ```bash
   python3 /www/wwwroot/pbn-tool/pbn_agent.py
   ```
2. Chạy ngầm liên tục (Daemon):
   ```bash
   nohup python3 /www/wwwroot/pbn-tool/pbn_agent.py --daemon > /www/wwwroot/pbn-tool/agent.log 2>&1 &
   ```
3. Đặt Crontab tự động (Mỗi 5 phút):
   ```bash
   */5 * * * * python3 /www/wwwroot/pbn-tool/pbn_agent.py >> /www/wwwroot/pbn-tool/agent.log 2>&1
   ```

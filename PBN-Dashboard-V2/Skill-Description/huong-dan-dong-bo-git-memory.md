# Hướng Dẫn Đồng Bộ GitHub & Bộ Nhớ Dùng Chung (PBN Git & Memory Sync)

Tài liệu này hướng dẫn cách cấu hình, sử dụng và tuân thủ quy trình đồng bộ mã nguồn, kỹ năng (skills), kế hoạch (plans) và bộ nhớ dùng chung (`MEMORY.md`) giữa các Agent và môi trường làm việc thông qua Git.

---

## 1. Lưu Trữ Token & Bảo Mật

Token truy cập GitHub được lưu trữ cục bộ tại file:
`C:\Users\Admin\Desktop\pbn-manangement\git_sync_config.json`

Nội dung cấu hình:
```json
{
  "repository": "https://github.com/linglengling/pbn-dashboard",
  "github_token": "<YOUR_GITHUB_TOKEN>",
  "branch": "main",
  "user": "linglengling"
}
```

> [!WARNING]
> **Quy Tắc Bảo Mật Token:**
> - File `git_sync_config.json` đã được đưa vào `.gitignore`.
> - Tuyệt đối không commit token hay file cấu hình này lên Git công khai. Nếu token bị lọt vào commit trên repo công khai, cơ chế bảo mật tự động của GitHub sẽ lập tức vô hiệu hóa (revoke) token chỉ trong vài giây.

---

## 2. Tiện Ích Đồng Bộ `scripts/git_sync.py`

Hệ thống đã xây dựng sẵn script `scripts/git_sync.py` (sử dụng thư viện chuẩn của Python) để tự động hóa:
- Tự động gắn token xác thực vào URL remote Git.
- Tự động sử dụng `git pull --rebase --autostash` để kéo code mới về mà không làm mất các thay đổi dở dang tại máy local.
- Tự động kiểm tra trạng thái và push các thay đổi đã hoàn thành lên GitHub.

### Bảng Lệnh Tiện Ích

| Lệnh | Ý nghĩa |
|---|---|
| `python scripts/git_sync.py status` | Xem trạng thái các file thay đổi tại local. |
| `python scripts/git_sync.py pull` | Kéo các cập nhật mới nhất từ GitHub về máy. |
| `python scripts/git_sync.py push "Ghi chú"` | Tự động `git add -A`, tạo commit và push lên `origin/main`. |
| `python scripts/git_sync.py sync "Ghi chú"` | Thực hiện tuần tự `pull` trước, sau đó `push`. |

---

## 3. Quy Chuẩn Đồng Bộ Bắt Buộc Đối Với Mọi Agent

1. **Trước khi bắt đầu nhiệm vụ:**
   - Luôn chạy `python scripts/git_sync.py pull` để nhận mọi cập nhật mới nhất mà người dùng hoặc các Agent khác (Hermes, OpenClaw...) vừa thực hiện.

2. **Cập nhật bộ nhớ dùng chung (`MEMORY.md`):**
   - File `MEMORY.md` tại thư mục gốc là nơi lưu trữ bối cảnh ngắn gọn phục vụ cho các phiên làm việc tiếp theo:
     - Các quy ước kỹ thuật mới (canonical files, rules mới).
     - Các domain đang chờ đổi DNS Cloudflare, các plan đang chờ duyệt.
     - Nhật ký ngắn các mốc công việc đã thực hiện thành công.

3. **Sau khi hoàn thành công việc:**
   - Khi có thay đổi về mã nguồn (`PBN-Dashboard-V2/`, `mu-plugins/`, `scripts/`), tài liệu kế hoạch (`PBN-Dashboard-V2/Skill-Description/`), kỹ năng (`.agents/skills/`) hoặc `MEMORY.md`:
   - Chạy `python scripts/git_sync.py push "<Nội dung commit ngắn gọn>"` để cập nhật ngay lên GitHub.

---

## 4. Các Tệp Tin Nghiêm Cấm Đưa Lên Git
- Các tệp cơ sở dữ liệu: `*.db`, `*.sqlite`, `*.sqlite-shm`, `*.sqlite-wal`.
- Các tệp nén sao lưu website: `*.tar.gz`, `*.zip`.
- Các file chứa token bí mật: `git_sync_config.json`, `github_token.json`, `*.token`.

---
name: pbn-git-sync
description: Tự động hóa đồng bộ mã nguồn, skills, plans và bộ nhớ dùng chung (MEMORY.md) lên GitHub qua token dự án (git_sync_config.json). Tự động pull cập nhật trước khi làm và push sau khi hoàn thành. Kích hoạt khi user yêu cầu "đồng bộ git", "git sync", "pull git", "push git", "lưu memory", "cập nhật repo", hoặc "/pbn-git-sync".
---

# PBN Git & Memory Sync Skill (`pbn-git-sync`)

Skill này chuẩn hóa và tự động hóa toàn bộ quy trình đồng bộ giữa môi trường làm việc local của Agent và kho lưu trữ trung tâm GitHub (`linglengling/pbn-dashboard`), đảm bảo mọi Agent (Antigravity, Hermes, OpenClaw...) và máy tính đều chia sẻ chung một trạng thái cập nhật nhất.

---

## 1. Cơ Chế Xác Thực & Quản Lý Token

- **File cấu hình token**: Lưu tại gốc dự án `git_sync_config.json`:
  ```json
  {
    "repository": "https://github.com/linglengling/pbn-dashboard",
    "github_token": "<YOUR_GITHUB_TOKEN>",
    "branch": "main",
    "user": "linglengling"
  }
  ```
- **Bảo mật tuyệt đối**:
  - `git_sync_config.json` và `*.token` đã được đưa vào `.gitignore`.
  - **TUYỆT ĐỐI KHÔNG** commit file cấu hình chứa token lên Git để tránh GitHub Secret Scanning tự động quét và thu hồi (revoke) token.
  - Script tiện ích `scripts/git_sync.py` tự động đọc token từ file này và gắn vào Git Remote URL khi thực hiện pull/push.

---

## 2. Quy Trình Đồng Bộ Chuẩn Cho Agent

### Bước 1: Pull trước khi thao tác (Pre-task Check)
Trước khi tiến hành bất kỳ chỉnh sửa nào (source code, thêm script, viết plan, thêm skill hoặc cập nhật memory):
```bash
python scripts/git_sync.py pull
```
*Lưu ý: Lệnh sử dụng `git pull --rebase --autostash` để tự động bảo lưu các thay đổi chưa commit nếu có và cập nhật commit mới nhất từ `origin/main`.*

### Bước 2: Thực hiện công việc & cập nhật bộ nhớ dùng chung
- **Nếu thay đổi kiến trúc, thêm site, phát hiện lỗi server hoặc quy ước kỹ thuật mới:**
  - Cập nhật ngay vào [MEMORY.md](file:///C:/Users/Admin/Desktop/pbn-manangement/MEMORY.md).
  - Tuân thủ cấu trúc 3 phần của `MEMORY.md`:
    1. *Quy ước kỹ thuật dùng chung mới nhất* (canonical source, rules).
    2. *Việc đang chờ / cần theo dõi (Pending)* (Cloudflare NS, lỗi domain, plan chờ duyệt).
    3. *Nhật ký ngắn các mốc gần nhất* (ghi theo ngày `YYYY-MM-DD`).
- **Nếu tạo hoặc cập nhật Skill / Plan:**
  - Skill mới lưu tại `.agents/skills/<tên-skill>/SKILL.md`.
  - Bắt buộc tạo tài liệu tiếng Việt song song tại `PBN-Dashboard-V2/Skill-Description/` theo Rule 6 của `AGENTS.md`.

### Bước 3: Push sau khi hoàn thành (Post-task Sync)
Ngay sau khi hoàn thành nhiệm vụ và kiểm tra hoạt động ổn định:
```bash
python scripts/git_sync.py push "<Thông điệp commit rõ ràng>"
```
Ví dụ:
```bash
python scripts/git_sync.py push "feat: add pbn-git-sync skill and update MEMORY.md"
```

---

## 3. Lệnh Thao Tác Nhanh Qua CLI

| Mục đích | Lệnh thực thi |
|---|---|
| Kiểm tra trạng thái Git | `python scripts/git_sync.py status` |
| Pull cập nhật mới nhất | `python scripts/git_sync.py pull` |
| Stage, commit và push | `python scripts/git_sync.py push "Nội dung commit"` |
| Cả Pull rồi Push luôn | `python scripts/git_sync.py sync "Nội dung commit"` |

---

## 4. Những Điều Cấm Tuyệt Đối Khi Đồng Bộ
1. **Không bao giờ push database**: Các file `*.db`, `*.sqlite`, `*.sqlite-shm`, `*.sqlite-wal` chứa dữ liệu nhạy cảm và token live của server.
2. **Không commit file backup dung lượng lớn**: `*.tar.gz`, `*.zip`.
3. **Không ghi đè hoặc vi phạm Whitelist**: `klao`, `init.php`, `wp-seo-rank-math.php` (xem chi tiết tại `AGENTS.md`).

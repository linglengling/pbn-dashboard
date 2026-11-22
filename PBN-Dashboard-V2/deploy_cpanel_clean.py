import os
import sys
import time
import sqlite3
import argparse
import paramiko

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LOCAL_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "VPS-client", "update-nwm-khoa-file-cpanel.py")
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pbn_matrix.db")

def log(msg):
    now = time.strftime("%H:%M:%S")
    clean = str(msg).encode("ascii", errors="replace").decode("ascii")
    print(f"[{now}] {clean}", flush=True)

def get_cpanel_servers():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM servers WHERE type = 'cpanel'").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def deploy_and_run(run_clean=False):
    servers = get_cpanel_servers()
    log(f"Tìm thấy {len(servers)} cPanel server trong database:")
    for s in servers:
        log(f"  - [{s['name']}] Host: {s['host']} | User: {s['username']}")

    for srv in servers:
        name = srv["name"]
        host = srv["host"]
        user = srv["username"]
        pwd = srv["password"]

        log(f"\n========================================================")
        log(f"Kết nối tới [{name}] ({host}, user: {user})...")
        log(f"========================================================")

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh.connect(host, username=user, password=pwd, timeout=20)
            
            # 1. Đảm bảo thư mục ~/pbn-tool tồn tại
            ssh.exec_command("mkdir -p ~/pbn-tool")
            
            # 2. Upload file script lên ~/pbn-tool/
            sftp = ssh.open_sftp()
            remote_target = "pbn-tool/update-nwm-khoa-file-cpanel.py"
            log(f"Uploading script to ~/{remote_target}...")
            sftp.put(LOCAL_SCRIPT, remote_target)
            sftp.close()

            # 3. Phân quyền thực thi
            ssh.exec_command("chmod +x ~/pbn-tool/update-nwm-khoa-file-cpanel.py")
            log(f"✅ Đã đưa script vào ~/pbn-tool/ trên {name}")

            # 4. Nếu có yêu cầu chạy clean
            if run_clean:
                log(f"🚀 Đang thực thi clean trên {name}...")
                cmd = "/usr/bin/python3 ~/pbn-tool/update-nwm-khoa-file-cpanel.py"
                stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True)
                for line in iter(stdout.readline, ""):
                    log(f"  [{name}] {line.rstrip()}")

            ssh.close()
        except Exception as e:
            log(f"❌ Lỗi trên [{name}]: {e}")

    log("\n🎉 Hoàn tất quy trình trên tất cả các server cPanel!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy & Run PBN Clean Tool on cPanel servers")
    parser.add_argument("--run", action="store_true", help="Chạy clean ngay sau khi deploy")
    args = parser.parse_args()

    deploy_and_run(run_clean=args.run)


#!/usr/bin/env python3
"""
PBN Git & Memory Sync Tool
Dong bo ma nguon, skills, plans va memory len GitHub repository.
Tu dong doc token tu git_sync_config.json de dam bao quyen truy cap.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT_DIR / "git_sync_config.json"


def find_git_binary():
    """Tim duong dan git.exe chuan nhat tren he thong."""
    candidates = [
        r"C:\Users\Admin\PortableGit\cmd\git.exe",
        r"C:\Program Files\Git\cmd\git.exe",
        shutil.which("git.exe"),
        shutil.which("git"),
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return "git"


GIT_BIN = find_git_binary()


def run_git(args, capture=False):
    """Chay lenh git trong thu muc goc cua du an."""
    cmd = [GIT_BIN] + args
    use_shell = GIT_BIN.lower().endswith((".cmd", ".bat"))
    try:
        if capture:
            res = subprocess.run(
                cmd,
                cwd=str(ROOT_DIR),
                capture_output=True,
                text=True,
                check=True,
                shell=use_shell,
            )
            return res.stdout.strip()
        else:
            res = subprocess.run(
                cmd,
                cwd=str(ROOT_DIR),
                check=True,
                shell=use_shell,
            )
            return res.returncode
    except subprocess.CalledProcessError as e:
        if capture:
            return e.stderr.strip()
        print(f"[ERROR] Git command failed: {' '.join(cmd)}", file=sys.stderr)
        return 1


def ensure_auth():
    """Kiem tra va cau hinh origin URL voi token va identity neu co."""
    # Dam bao user name va email da duoc set
    try:
        user_name = run_git(["config", "user.name"], capture=True)
        if not user_name or "error" in user_name.lower():
            run_git(["config", "user.name", "linglengling"])
        user_email = run_git(["config", "user.email"], capture=True)
        if not user_email or "error" in user_email.lower():
            run_git(["config", "user.email", "linglengling@users.noreply.github.com"])
    except Exception:
        pass

    if not CONFIG_FILE.exists():
        return
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        token = cfg.get("github_token", "").strip()
        repo = cfg.get("repository", "").strip()
        if token and repo:
            clean_repo = repo.replace("https://", "").rstrip("/")
            if not clean_repo.endswith(".git"):
                clean_repo += ".git"
            auth_url = f"https://{token}@{clean_repo}"
            current_remote = run_git(["remote", "get-url", "origin"], capture=True)
            if current_remote != auth_url:
                run_git(["remote", "set-url", "origin", auth_url])
    except Exception as e:
        print(f"[WARN] Khong the cau hinh token tu {CONFIG_FILE.name}: {e}")


def pull():
    """Kiem tra va pull cac thay doi moi nhat ve local (dung autostash neu co uncommitted changes)."""
    ensure_auth()
    print("[INFO] Kiem tra va cap nhat ma nguon tu GitHub (git pull --rebase --autostash)...")
    res = run_git(["pull", "--rebase", "--autostash", "origin", "main"])
    return res


def pull_server():
    """Ket noi SSH toi VPS 103.106.105.77 va pull tai workspace chung /www/wwwroot/phn-manage.sites/src-github."""
    # Neu dang chay truc tiep tren server tai chinh thu muc nay thi khong can SSH
    if os.path.exists("/www/wwwroot/phn-manage.sites/src-github"):
        if str(ROOT_DIR) == "/www/wwwroot/phn-manage.sites/src-github":
            return pull()

    print("[INFO] Dong bo workspace chung tren server 103.106.105.77 (/www/wwwroot/phn-manage.sites/src-github)...")
    try:
        import paramiko
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect("103.106.105.77", username="root", password="q9icdLH1!*0B", timeout=15)
        cmd = "cd /www/wwwroot/phn-manage.sites/src-github && python3 scripts/git_sync.py pull"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        out = stdout.read().decode("utf-8", errors="ignore").strip()
        err = stderr.read().decode("utf-8", errors="ignore").strip()
        ssh.close()
        if out:
            print(f"[SERVER OUT] {out}")
        if err and "error" in err.lower():
            print(f"[SERVER ERR] {err}")
        print("[SUCCESS] Da pull thanh cong tai workspace server!")
        return 0
    except Exception as e:
        print(f"[WARN] Khong the tu dong pull server qua SSH (bo qua neu offline hoac da chay truc tiep): {e}")
        return 1


def push(message: str, sync_server_after: bool = True):
    """Stage tat ca file hop le, commit (neu co thay doi) va push unpushed commits len GitHub."""
    ensure_auth()
    if not message:
        message = "Update source code, skills, plans and shared memory"

    print("[INFO] Staging thay doi...")
    run_git(["add", "-A"])

    status_out = run_git(["status", "--porcelain"], capture=True)
    if status_out:
        print(f"[INFO] Commit voi thong diep: '{message}'")
        run_git(["commit", "-m", message])
    else:
        print("[INFO] Khong co thay doi unstaged nao can commit moi.")

    # Kiem tra xem co commit nao chua push len remote khong
    unpushed = run_git(["log", "@{u}..HEAD", "--oneline"], capture=True)
    if unpushed:
        print(f"[INFO] Phat hien cac commit chua push:\n{unpushed}")
        print("[INFO] Dang push len origin/main...")
        res = run_git(["push", "origin", "main"])
        if res == 0:
            print("[SUCCESS] Dong bo len GitHub thanh cong!")
            if sync_server_after:
                pull_server()
        return res
    else:
        print("[INFO] Repository da dong bo hoan toan voi origin/main.")
        if sync_server_after:
            pull_server()
        return 0


def sync(message: str):
    """Thuc hien ca 2 buoc: pull truoc, sau do push cac thay doi va cap nhat server."""
    pull_res = pull()
    if pull_res != 0:
        print("[WARN] Git pull gap van de, hay kiem tra conflict truoc khi push.")
        return pull_res
    return push(message, sync_server_after=True)


def status():
    """Kiem tra trang thai git."""
    run_git(["status"])


def main():
    action = sys.argv[1].lower() if len(sys.argv) > 1 else "status"
    msg = sys.argv[2] if len(sys.argv) > 2 else ""

    if action == "pull":
        sys.exit(pull())
    elif action == "push":
        sys.exit(push(msg))
    elif action == "sync":
        sys.exit(sync(msg))
    elif action == "pull-server":
        sys.exit(pull_server())
    elif action == "status":
        sys.exit(status())
    else:
        print(f"Usage: python {Path(__file__).name} [pull|push|sync|pull-server|status] [commit_message]")
        sys.exit(1)


if __name__ == "__main__":
    main()

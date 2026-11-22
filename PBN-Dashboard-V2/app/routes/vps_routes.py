import hashlib
import time
import json
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from ..database import get_db, log_activity, get_settings, set_setting
from ..auth import get_current_user

router = APIRouter(prefix="/api/vps", tags=["vps"])

DEFAULT_SECRET_SALT = "pbn_s3cr3t_k3y_2024_change_this"

def get_active_secret_salt():
    st = get_settings()
    return st.get("SECRET_SALT") or DEFAULT_SECRET_SALT

class VPSSignalRequest(BaseModel):
    server_ip: str
    token: str
    timestamp: int
    metrics: Optional[Dict[str, Any]] = None

@router.post("/signal")
def receive_vps_signal(req: VPSSignalRequest):
    # Verify timestamp freshness (max 10 min drift)
    if abs(int(time.time()) - req.timestamp) > 600:
        raise HTTPException(status_code=403, detail="Tín hiệu đã hết hạn")

    # Verify signature
    salt = get_active_secret_salt()
    expected = hashlib.md5(f"{req.server_ip}{req.timestamp}{salt}".encode()).hexdigest()
    if not (expected.lower() == req.token.lower()):
        raise HTTPException(status_code=403, detail="Chữ ký xác thực không hợp lệ")

    now = time.strftime("%Y-%m-%d %H:%M:%S")
    server_name = req.server_ip

    with get_db() as conn:
        # Match server by host
        row = conn.execute("SELECT id, name, host FROM servers WHERE host = ? OR host LIKE ?", 
                           (req.server_ip, f"%{req.server_ip}%")).fetchone()

        wp_count = req.metrics.get("wp_sites_count") if req.metrics else None

        if row:
            server_name = row["name"]
            if wp_count is not None and wp_count > 0:
                conn.execute("""
                    UPDATE servers SET 
                        status = 'ONLINE', 
                        last_checked = ?, 
                        sites_count = ?,
                        error_message = NULL 
                    WHERE id = ?
                """, (now, wp_count, row["id"]))
            else:
                conn.execute("""
                    UPDATE servers SET 
                        status = 'ONLINE', 
                        last_checked = ?, 
                        error_message = NULL 
                    WHERE id = ?
                """, (now, row["id"]))
            conn.commit()

    return {
        "success": True,
        "message": f"Tín hiệu từ VPS '{server_name}' ({req.server_ip}) đã được ghi nhận thành công!",
        "server_name": server_name,
        "recorded_at": now
    }

class VPSSyncSitesRequest(BaseModel):
    server_ip: str
    token: str
    timestamp: int
    sites: list

@router.post("/sync-sites")
def sync_vps_sites_endpoint(req: VPSSyncSitesRequest):
    import socket
    from ..server_runner import sync_scanned_sites

    # Verify timestamp freshness (max 10 min drift)
    if abs(int(time.time()) - req.timestamp) > 600:
        raise HTTPException(status_code=403, detail="Tín hiệu đã hết hạn")

    # Verify signature
    salt = get_active_secret_salt()
    expected = hashlib.md5(f"{req.server_ip}{req.timestamp}{salt}".encode()).hexdigest()
    if not (expected.lower() == req.token.lower()):
        raise HTTPException(status_code=403, detail="Chữ ký xác thực không hợp lệ")

    with get_db() as conn:
        all_srvs = conn.execute("SELECT id, name, host, type FROM servers").fetchall()
        srv = None
        # 1. Match host string directly
        for s in all_srvs:
            if s["host"] == req.server_ip or req.server_ip in s["host"]:
                srv = dict(s)
                break
        
        # 2. Match by DNS resolving hostname to IP
        if not srv:
            for s in all_srvs:
                try:
                    resolved_ip = socket.gethostbyname(s["host"])
                    if resolved_ip == req.server_ip:
                        srv = dict(s)
                        break
                except Exception:
                    pass

        if not srv:
            raise HTTPException(status_code=404, detail=f"Không tìm thấy máy chủ cho IP {req.server_ip}")

    synced_count = sync_scanned_sites(srv, req.sites)

    log_activity(
        "cron",
        "auto_scan_sites",
        {
            "server_name": srv["name"],
            "server_host": srv["host"],
            "total_scanned": len(req.sites),
            "synced_new": synced_count
        }
    )

    return {
        "success": True,
        "server_name": srv["name"],
        "server_host": srv["host"],
        "total_scanned": len(req.sites),
        "synced_count": synced_count,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

# --- CRONS & CLIENT NODES MANAGEMENT ---

@router.get("/crons-overview")
def get_crons_overview(current_user: dict = Depends(get_current_user)):
    """Returns overview of client cron runs, recent heartbeat pings, and settings"""
    with get_db() as conn:
        servers = conn.execute("""
            SELECT id, name, type, host, port, username, status, sites_count, last_checked, error_message, created_at 
            FROM servers ORDER BY id ASC
        """).fetchall()

        # Recent activities related to cron / sync
        logs = conn.execute("""
            SELECT id, target_domain, action, details, created_at 
            FROM activity_log 
            WHERE action IN ('auto_scan_sites', 'site_synced', 'cron', 'cron_scan') 
               OR target_domain = 'cron'
            ORDER BY created_at DESC LIMIT 20
        """).fetchall()

        # Recent pings from WP sites
        recent_pings = conn.execute("""
            SELECT domain, ip, status, last_seen, server_host, total_homepage_links 
            FROM sites 
            ORDER BY last_seen DESC LIMIT 15
        """).fetchall()

    st = get_settings()

    return {
        "success": True,
        "servers": [dict(s) for s in servers],
        "recent_cron_logs": [dict(l) for l in logs],
        "recent_pings": [dict(p) for p in recent_pings],
        "settings": {
            "SECRET_SALT": st.get("SECRET_SALT") or DEFAULT_SECRET_SALT,
            "HEARTBEAT_INTERVAL": st.get("HEARTBEAT_INTERVAL") or "300",
            "CRON_SCHEDULE_EXPR": st.get("CRON_SCHEDULE_EXPR") or "0 3 */3 * *",
            "AUTO_AUDIT_ENABLED": st.get("AUTO_AUDIT_ENABLED") or "1",
            "AUTO_AUDIT_NOTIFY_LOGIN": st.get("AUTO_AUDIT_NOTIFY_LOGIN") or "1",
            "LAST_AUDIT_RUN": st.get("LAST_AUDIT_RUN") or "",
            "LAST_AUDIT_REPORT": json.loads(st.get("LAST_AUDIT_REPORT")) if st.get("LAST_AUDIT_REPORT") else None
        }
    }

class VpsSettingsUpdateRequest(BaseModel):
    SECRET_SALT: Optional[str] = None
    HEARTBEAT_INTERVAL: Optional[str] = None
    CRON_SCHEDULE_EXPR: Optional[str] = None
    AUTO_AUDIT_ENABLED: Optional[str] = None
    AUTO_AUDIT_NOTIFY_LOGIN: Optional[str] = None

@router.post("/settings")
def update_vps_settings(req: VpsSettingsUpdateRequest, current_user: dict = Depends(get_current_user)):
    """Updates client & cron settings"""
    if req.SECRET_SALT is not None:
        set_setting("SECRET_SALT", req.SECRET_SALT.strip())
    if req.HEARTBEAT_INTERVAL is not None:
        set_setting("HEARTBEAT_INTERVAL", req.HEARTBEAT_INTERVAL.strip())
    if req.CRON_SCHEDULE_EXPR is not None:
        set_setting("CRON_SCHEDULE_EXPR", req.CRON_SCHEDULE_EXPR.strip())
    if req.AUTO_AUDIT_ENABLED is not None:
        set_setting("AUTO_AUDIT_ENABLED", req.AUTO_AUDIT_ENABLED.strip())
    if req.AUTO_AUDIT_NOTIFY_LOGIN is not None:
        set_setting("AUTO_AUDIT_NOTIFY_LOGIN", req.AUTO_AUDIT_NOTIFY_LOGIN.strip())

    return {"success": True, "message": "Đã lưu cấu hình máy con & Crontask thành công!"}

class TriggerCronRequest(BaseModel):
    server_id: int

@router.post("/trigger-remote-cron")
def trigger_remote_cron_endpoint(req: TriggerCronRequest, current_user: dict = Depends(get_current_user)):
    """Remotely executes auto_scan_sites.py on the specified server via SSH"""
    from ..server_runner import run_remote_cron
    with get_db() as conn:
        row = conn.execute("SELECT * FROM servers WHERE id = ?", (req.server_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Không tìm thấy máy chủ")
        server = dict(row)

    res = run_remote_cron(server)
    if res.get("success"):
        log_activity(
            "cron",
            "manual_trigger_scan",
            {
                "server_id": server["id"],
                "server_name": server["name"],
                "server_host": server["host"]
            }
        )
    return res

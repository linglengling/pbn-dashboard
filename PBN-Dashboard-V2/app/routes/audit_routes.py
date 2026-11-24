import json
import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from ..auth import get_current_user
from ..database import get_db, get_sites, get_settings, set_setting
from ..audit_runner import (
    audit_single_domain,
    audit_batch_domains,
    get_audit_summary,
    fix_domain_noindex,
    run_system_audit_job
)

router = APIRouter(prefix="/api/audit", tags=["audit"])

class ScanRequest(BaseModel):
    domains: Optional[List[str]] = None
    scan_all: Optional[bool] = False
    filter_status: Optional[str] = None  # 'ALL', 'OFFLINE', 'UNAUDITED'
    limit: Optional[int] = 100

class FixIndexRequest(BaseModel):
    domains: List[str]

@router.get("/summary")
def audit_summary(current_user: dict = Depends(get_current_user)):
    data = get_audit_summary()
    return {"success": True, "data": data}

@router.get("/sites")
def list_audited_sites(
    filter_type: Optional[str] = "ISSUES",  # 'ISSUES', 'NOINDEX', 'ERROR', 'HEALTHY', 'ALL'
    error_type: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 200,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    with get_db() as conn:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        query = "SELECT * FROM site_audits"
        clauses = []
        params = []

        if filter_type == "ISSUES":
            clauses.append("(is_noindex = 1 OR (error_type IS NOT NULL AND error_type != 'NONE'))")
        elif filter_type == "NOINDEX":
            clauses.append("is_noindex = 1")
        elif filter_type == "ERROR":
            clauses.append("(error_type IS NOT NULL AND error_type NOT IN ('NONE', 'NOINDEX'))")
        elif filter_type == "HEALTHY":
            clauses.append("error_type = 'NONE' AND is_noindex = 0")

        if error_type and error_type != "ALL":
            clauses.append("error_type = ?")
            params.append(error_type)

        if search:
            clauses.append("(domain LIKE ? OR title LIKE ? OR error_detail LIKE ?)")
            s_param = f"%{search.strip()}%"
            params.extend([s_param, s_param, s_param])

        if clauses:
            query += " WHERE " + " AND ".join(clauses)

        query += " ORDER BY audited_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = conn.execute(query, params).fetchall()
        
        # Count total matching
        count_q = "SELECT COUNT(*) FROM site_audits"
        if clauses:
            count_q += " WHERE " + " AND ".join(clauses)
        total_matched = conn.execute(count_q, params[:-2] if params else []).fetchone()["COUNT(*)"]

        return {
            "success": True,
            "data": rows,
            "total": total_matched,
            "limit": limit,
            "offset": offset
        }

@router.post("/scan")
def start_scan(req: ScanRequest, current_user: dict = Depends(get_current_user)):
    target_domains = []

    if req.domains and len(req.domains) > 0:
        target_domains = [d.strip() for d in req.domains if d.strip()]
    elif req.scan_all or req.filter_status:
        all_sites = get_sites(include_pending=False)
        with get_db() as conn:
            audited = set(r[0] for r in conn.execute("SELECT domain FROM site_audits").fetchall())

        if req.filter_status == "UNAUDITED":
            target_domains = [s["domain"] for s in all_sites if s["domain"] not in audited]
        elif req.filter_status == "OFFLINE":
            target_domains = [s["domain"] for s in all_sites if s.get("status") == "OFFLINE"]
        else:
            target_domains = [s["domain"] for s in all_sites]
            
        if req.limit and len(target_domains) > req.limit:
            target_domains = target_domains[:req.limit]
    else:
        # Default scan first 50 sites
        all_sites = get_sites(include_pending=False)
        target_domains = [s["domain"] for s in all_sites[:50]]

    if not target_domains:
        return {"success": False, "message": "Không có domain nào để quét", "scanned": 0}

    results = audit_batch_domains(target_domains, max_workers=25)
    summary = get_audit_summary()

    return {
        "success": True,
        "scanned": len(results),
        "results": results[:50],  # Return preview
        "summary": summary,
        "message": f"Đã hoàn thành kiểm tra {len(results)} website thành công!"
    }

@router.post("/fix-index")
def bulk_fix_index(req: FixIndexRequest, current_user: dict = Depends(get_current_user)):
    if not req.domains:
        raise HTTPException(status_code=400, detail="Vui lòng cung cấp danh sách domain cần mở index")

    results = []
    with ThreadPoolExecutor(max_workers=15) as executor:
        for res in executor.map(fix_domain_noindex, req.domains):
            results.append(res)

    success_count = sum(1 for r in results if r.get("success"))
    summary = get_audit_summary()

    return {
        "success": True,
        "fixed_count": success_count,
        "total_requested": len(req.domains),
        "results": results,
        "summary": summary,
        "message": f"Đã gửi lệnh mở index thành công tới {success_count}/{len(req.domains)} website!"
    }

class AuditToggleIndexRequest(BaseModel):
    domains: List[str]
    action: str  # "open" or "close"

@router.post("/toggle-index")
def audit_toggle_index(req: AuditToggleIndexRequest, current_user: dict = Depends(get_current_user)):
    from ..audit_runner import toggle_domain_index
    if not req.domains:
        raise HTTPException(status_code=400, detail="Vui lòng cung cấp danh sách domain")

    action = req.action.lower().strip()
    if action not in ["open", "close"]:
        raise HTTPException(status_code=400, detail="Action phải là 'open' hoặc 'close'")

    results = []
    with ThreadPoolExecutor(max_workers=15) as executor:
        for res in executor.map(lambda d: toggle_domain_index(d, action), req.domains):
            results.append(res)

    success_count = sum(1 for r in results if r.get("success"))
    summary = get_audit_summary()

    action_text = "mở index (Cho phép Google index)" if action == "open" else "đóng index (Chặn tìm kiếm / NoIndex)"
    if success_count == 0:
        failed = [r for r in results if not r.get("success")]
        first_err = failed[0].get("error") if failed else ""
        return {
            "success": False,
            "action": action,
            "updated_count": 0,
            "total": len(req.domains),
            "results": results,
            "summary": summary,
            "message": f"Không thể {action_text} cho {len(req.domains)} website" + (f": {first_err}" if first_err else "")
        }

    return {
        "success": True,
        "action": action,
        "updated_count": success_count,
        "total": len(req.domains),
        "results": results,
        "summary": summary,
        "message": f"Đã {action_text} thành công cho {success_count}/{len(req.domains)} website!"
    }

# ============================================================
# CRON SYSTEM AUDIT & LOGIN NOTIFICATION REPORT
# ============================================================

@router.get("/login-report")
def get_login_report(current_user: dict = Depends(get_current_user)):
    """
    Called upon user login or dashboard load.
    Returns the latest audit report if unread and there are site errors.
    """
    st = get_settings()
    if st.get("AUTO_AUDIT_NOTIFY_LOGIN", "1") != "1":
        return {"has_report": False, "unread": False}

    is_unread = st.get("LAST_AUDIT_REPORT_UNREAD", "1") == "1"

    report_json = st.get("LAST_AUDIT_REPORT")
    if not report_json:
        # Fallback: check current errors directly from site_audits
        summary = get_audit_summary()
        if summary.get("errors", 0) > 0:
            with get_db() as conn:
                conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
                err_rows = conn.execute("""
                    SELECT domain, error_type, error_detail, http_status, title, audited_at
                    FROM site_audits
                    WHERE error_type NOT IN ('NONE', 'NOINDEX')
                    ORDER BY audited_at DESC LIMIT 50
                """).fetchall()
            return {
                "has_report": True,
                "unread": is_unread,
                "report": {
                    "timestamp": summary.get("last_audit_at") or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "total_scanned": summary.get("total_audited", 0),
                    "healthy": summary.get("healthy", 0),
                    "noindex": summary.get("noindex", 0),
                    "errors": summary.get("errors", 0),
                    "breakdown": summary.get("breakdown", {}),
                    "error_sites": err_rows
                }
            }
        return {"has_report": False, "unread": False}

    try:
        report = json.loads(report_json)
    except Exception:
        return {"has_report": False, "unread": False}

    return {
        "has_report": True,
        "unread": is_unread,
        "report": report
    }

@router.post("/dismiss-report")
def dismiss_report(current_user: dict = Depends(get_current_user)):
    """Marks the latest audit report as read"""
    set_setting("LAST_AUDIT_REPORT_UNREAD", "0")
    return {"success": True, "message": "Đã đánh dấu đã đọc báo cáo"}

@router.post("/run-system-audit")
def trigger_manual_system_audit(background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    """Manually triggers a full system error scan in the background"""
    background_tasks.add_task(run_system_audit_job)
    return {
        "success": True,
        "message": "Đã kích hoạt quét toàn bộ website trong hệ thống! Kết quả sẽ được cập nhật trong báo cáo."
    }

@router.post("/run-scheduled-cron")
def run_scheduled_cron(request: Request, background_tasks: BackgroundTasks):
    """
    Triggered by system crontab (e.g. 0 18 * * * (VN days 1,6,11,16,21,26,31)) or internal scheduler.
    Performs full site error check.
    """
    client_ip = request.client.host if request.client else ""
    # Allow localhost or authenticated calls
    background_tasks.add_task(run_system_audit_job)
    return {
        "success": True,
        "message": f"Đã nhận lệnh kích hoạt cron từ {client_ip}. Tiến trình quét đang chạy trong nền."
    }

class BulkAuditDomainsRequest(BaseModel):
    domains: List[str]

@router.post("/bulk-clear-errors")
def bulk_clear_errors(req: BulkAuditDomainsRequest, current_user: dict = Depends(get_current_user)):
    """Resets audit error status for the specified domains"""
    if not req.domains:
        raise HTTPException(status_code=400, detail="Vui lòng cung cấp danh sách domain")

    with get_db() as conn:
        placeholders = ','.join(['?'] * len(req.domains))
        conn.execute(f"""
            UPDATE site_audits SET 
                error_type = 'NONE', 
                error_detail = NULL, 
                http_status = 200,
                audited_at = datetime('now', 'localtime')
            WHERE domain IN ({placeholders})
        """, req.domains)
        conn.commit()

    return {
        "success": True,
        "cleared_count": len(req.domains),
        "message": f"Đã xóa trạng thái lỗi cho {len(req.domains)} website thành công!"
    }

@router.post("/bulk-delete-sites")
def bulk_delete_sites(req: BulkAuditDomainsRequest, current_user: dict = Depends(get_current_user)):
    """Permanently deletes the specified domains from sites, site_audits, backlinks, and posts"""
    if not req.domains:
        raise HTTPException(status_code=400, detail="Vui lòng cung cấp danh sách domain cần xóa")

    with get_db() as conn:
        placeholders = ','.join(['?'] * len(req.domains))
        conn.execute(f"DELETE FROM sites WHERE domain IN ({placeholders})", req.domains)
        conn.execute(f"DELETE FROM site_audits WHERE domain IN ({placeholders})", req.domains)
        conn.execute(f"DELETE FROM backlinks WHERE site_domain IN ({placeholders})", req.domains)
        conn.execute(f"DELETE FROM posts WHERE site_domain IN ({placeholders})", req.domains)
        conn.commit()

    return {
        "success": True,
        "deleted_count": len(req.domains),
        "message": f"Đã xóa hoàn toàn {len(req.domains)} website khỏi hệ thống!"
    }

@router.post("/clean-invalid-domains")
def clean_invalid_domains_endpoint(current_user: dict = Depends(get_current_user)):
    """Automatically cleans all non-domain entries (e.g. cPanel folder names without dots)"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT domain FROM sites")
        site_doms = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT domain FROM site_audits")
        audit_doms = [r[0] for r in cur.fetchall()]

        all_doms = set(site_doms + audit_doms)
        invalid = []
        for d in all_doms:
            if not d or not isinstance(d, str):
                invalid.append(d)
                continue
            d_clean = d.strip().lower()
            if ' ' in d_clean or '/' in d_clean or '\\' in d_clean or ':' in d_clean:
                invalid.append(d)
                continue
            parts = d_clean.split('.')
            if len(parts) < 2 or not parts[0] or not parts[-1] or len(parts[-1]) < 2 or not parts[-1].isalpha():
                invalid.append(d)

        if invalid:
            placeholders = ','.join(['?'] * len(invalid))
            conn.execute(f"DELETE FROM sites WHERE domain IN ({placeholders})", invalid)
            conn.execute(f"DELETE FROM site_audits WHERE domain IN ({placeholders})", invalid)
            conn.execute(f"DELETE FROM backlinks WHERE site_domain IN ({placeholders})", invalid)
            conn.execute(f"DELETE FROM posts WHERE site_domain IN ({placeholders})", invalid)
            conn.commit()

    return {
        "success": True,
        "cleaned_count": len(invalid),
        "message": f"Đã quét và xóa {len(invalid)} tên không đúng định dạng domain!"
    }




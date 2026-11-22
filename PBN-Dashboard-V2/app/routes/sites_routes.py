from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List, Any
from ..database import (
    get_sites, get_pending_sites, get_site_detail,
    approve_sites, reject_sites, record_site_ping, log_activity
)
from ..auth import get_current_user

router = APIRouter(prefix="/api/sites", tags=["sites"])

class ApproveRequest(BaseModel):
    domain: Optional[str] = None
    domains: Optional[List[str]] = None

class RejectRequest(BaseModel):
    domain: Optional[str] = None
    domains: Optional[List[str]] = None
    delete_permanently: Optional[bool] = False

@router.get("")
def list_sites(include_pending: bool = False, server_id: Optional[int] = None, current_user: dict = Depends(get_current_user)):
    data = get_sites(include_pending=include_pending, server_id=server_id)
    return {"success": True, "data": data}

@router.get("/pending")
def list_pending(current_user: dict = Depends(get_current_user)):
    data = get_pending_sites()
    return {"success": True, "data": data}

@router.get("/{domain}")
def site_detail(domain: str, current_user: dict = Depends(get_current_user)):
    data = get_site_detail(domain)
    if not data:
        raise HTTPException(status_code=404, detail="Site không tồn tại")
    return {"success": True, "data": data}

@router.post("/approve")
def approve_endpoint(req: ApproveRequest, current_user: dict = Depends(get_current_user)):
    list_doms = req.domains or ([req.domain] if req.domain else [])
    if not list_doms:
        raise HTTPException(status_code=400, detail="Vui lòng cung cấp ít nhất 1 domain cần duyệt")
    approve_sites(list_doms)
    for d in list_doms:
        log_activity(d, "site_approved", {"user": current_user["username"]})
    return {"success": True, "message": f"Đã phê duyệt {len(list_doms)} site thành công!", "approved": list_doms}

@router.post("/reject")
def reject_endpoint(req: RejectRequest, current_user: dict = Depends(get_current_user)):
    list_doms = req.domains or ([req.domain] if req.domain else [])
    if not list_doms:
        raise HTTPException(status_code=400, detail="Vui lòng cung cấp ít nhất 1 domain cần từ chối")
    reject_sites(list_doms, delete_permanently=bool(req.delete_permanently))
    for d in list_doms:
        log_activity(d, "site_rejected", {"user": current_user["username"], "permanent": req.delete_permanently})
    return {"success": True, "message": f"Đã xử lý từ chối {len(list_doms)} site thành công!", "rejected": list_doms}

@router.post("/ping")
async def ping_endpoint(req: Request):
    try:
        body = await req.json()
    except Exception:
        body = dict(await req.form())
    
    # Extract client IP
    client_ip = req.headers.get("x-forwarded-for") or req.client.host if req.client else "unknown"
    if not body.get("ip"):
        body["ip"] = client_ip
        
    res = record_site_ping(body)
    return res

@router.post("/check-redirects")
def check_all_redirects(current_user: dict = Depends(get_current_user)):
    import os, sys
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)

    try:
        from scan_301_redirects import check_domain_redirect
    except Exception:
        # Fallback if imported from parent
        from ..scan_301_redirects import check_domain_redirect

    from concurrent.futures import ThreadPoolExecutor
    from ..database import get_db, get_sites

    sites = get_sites(include_pending=False)
    domains = [s["domain"] for s in sites]

    redirects_found = {}
    direct_domains = []

    with ThreadPoolExecutor(max_workers=40) as executor:
        for dom, target in executor.map(check_domain_redirect, domains):
            if target:
                redirects_found[dom] = target
            else:
                direct_domains.append(dom)

    with get_db() as conn:
        for dom, target in redirects_found.items():
            conn.execute("UPDATE sites SET redirect_to = ?, updated_at = datetime('now', 'localtime') WHERE domain = ?", (target, dom))

        for i in range(0, len(direct_domains), 500):
            batch = direct_domains[i:i+500]
            placeholders = ",".join(["?"] * len(batch))
            conn.execute(f"UPDATE sites SET redirect_to = NULL WHERE domain IN ({placeholders}) AND redirect_to IS NOT NULL", batch)
        conn.commit()

    return {
        "success": True,
        "total_checked": len(domains),
        "total_redirects": len(redirects_found),
        "redirects": redirects_found,
        "message": f"Đã quét xong: Phát hiện và nhóm {len(redirects_found)} domain 301 Redirect trên {len(domains)} domain!"
    }

class ToggleIndexRequest(BaseModel):
    domain: Optional[str] = None
    domains: Optional[List[str]] = None
    action: str  # "open" (blog_public = 1) or "close" (blog_public = 0)

@router.post("/toggle-index")
def toggle_index_endpoint(req: ToggleIndexRequest, current_user: dict = Depends(get_current_user)):
    targets = req.domains or ([req.domain] if req.domain else [])
    if not targets:
        raise HTTPException(status_code=400, detail="Vui lòng cung cấp danh sách ít nhất 1 domain")

    action = req.action.lower().strip()
    if action not in ["open", "close"]:
        raise HTTPException(status_code=400, detail="Action phải là 'open' hoặc 'close'")

    from concurrent.futures import ThreadPoolExecutor
    from ..audit_runner import toggle_domain_index

    results = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        for res in executor.map(lambda d: toggle_domain_index(d, action), targets):
            results.append(res)

    success_count = sum(1 for r in results if r.get("success"))
    action_text = "mở index (Cho phép Google index)" if action == "open" else "đóng index (Chặn tìm kiếm / NoIndex)"
    return {
        "success": True,
        "action": action,
        "updated_count": success_count,
        "total": len(targets),
        "results": results,
        "message": f"Đã {action_text} thành công cho {success_count}/{len(targets)} website!"
    }

class UpdateClusterRequest(BaseModel):
    site_domains: Optional[List[str]] = None
    domains: Optional[List[str]] = None
    domain: Optional[str] = None
    domain_text: Optional[str] = None
    cluster: str
    color: Optional[str] = None

@router.post("/update-clusters")
def update_clusters_endpoint(req: UpdateClusterRequest, current_user: dict = Depends(get_current_user)):
    import re
    from ..database import update_sites_cluster

    targets = []
    if req.domains:
        targets.extend(req.domains)
    if req.site_domains:
        targets.extend(req.site_domains)
    if req.domain:
        targets.append(req.domain)
    if req.domain_text:
        tokens = re.split(r'[\r\n,;\s]+', req.domain_text)
        targets.extend([t.strip() for t in tokens if t.strip()])

    targets = list(dict.fromkeys(targets))
    if not targets:
        raise HTTPException(status_code=400, detail="Vui lòng cung cấp danh sách ít nhất 1 domain cần gán cụm cluster")

    cluster_name = req.cluster.strip()
    if not cluster_name:
        raise HTTPException(status_code=400, detail="Vui lòng nhập tên cụm cluster")

    updated_count, clean_domains = update_sites_cluster(targets, cluster_name, color=req.color)
    return {
        "success": True,
        "cluster": cluster_name,
        "updated_count": updated_count,
        "total_requested": len(clean_domains),
        "message": f"Đã gán thành công {updated_count} website vào cụm cluster '{cluster_name}'!"
    }

class ScanLinksRequest(BaseModel):
    domain: str

@router.post("/scan-links")
def scan_site_links_endpoint(req: ScanLinksRequest, current_user: dict = Depends(get_current_user)):
    """Triggers real-time crawler on the homepage of a specific site to extract all outbound links"""
    from ..audit_runner import audit_single_domain
    domain = req.domain.strip()
    if not domain:
        raise HTTPException(status_code=400, detail="Vui lòng cung cấp domain")

    res = audit_single_domain(domain)
    return {
        "success": True,
        "domain": domain,
        "total_homepage_links": res.get("total_outbound_links", 0),
        "homepage_outbound_links": res.get("outbound_links", [])
    }

class CaptureScreenshotRequest(BaseModel):
    domain: str

@router.post("/capture-screenshot")
def capture_screenshot_endpoint(req: CaptureScreenshotRequest, current_user: dict = Depends(get_current_user)):
    """Triggers instant screenshot request for a domain with cache-busting timestamp"""
    from ..database import get_db
    import time, urllib.request, threading

    domain = req.domain.replace("http://", "").replace("https://", "").strip().rstrip("/")
    if not domain:
        raise HTTPException(status_code=400, detail="Vui lòng cung cấp domain")

    ts = int(time.time())
    new_url = f"https://s0.wp.com/mshots/v1/https%3A%2F%2F{domain}?w=1280&h=800&v={ts}"

    def ping_mshots():
        try:
            mshot_url = f"https://s0.wp.com/mshots/v1/https%3A%2F%2F{domain}?w=600&h=400&v={ts}"
            req_obj = urllib.request.Request(mshot_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            urllib.request.urlopen(req_obj, timeout=8)
        except Exception:
            pass

    threading.Thread(target=ping_mshots, daemon=True).start()

    with get_db() as conn:
        try:
            conn.execute("UPDATE sites SET screenshot_url = ? WHERE domain = ?", (new_url, domain))
        except Exception:
            pass
        conn.execute("""
            INSERT INTO site_audits (domain, screenshot_url, audited_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(domain) DO UPDATE SET
                screenshot_url = excluded.screenshot_url,
                audited_at = CURRENT_TIMESTAMP
        """, (domain, new_url))
        conn.commit()

    return {
        "success": True,
        "domain": domain,
        "screenshot_url": new_url,
        "message": f"Đã gửi yêu cầu chụp ảnh màn hình cho {domain}!"
    }


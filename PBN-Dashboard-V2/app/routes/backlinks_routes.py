import requests
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..database import get_all_backlinks, insert_backlink, delete_backlink, log_activity, get_db
from ..auth import get_current_user

router = APIRouter(prefix="/api/backlinks", tags=["backlinks"])

class BacklinkInsertRequest(BaseModel):
    site_domain: str
    target_url: str
    anchor_text: str
    post_id: Optional[int] = None
    post_url: Optional[str] = None

@router.get("")
def list_backlinks(current_user: dict = Depends(get_current_user)):
    data = get_all_backlinks()
    return {"success": True, "data": data}

@router.post("")
def add_backlink(req: BacklinkInsertRequest, current_user: dict = Depends(get_current_user)):
    bid = insert_backlink(
        site_domain=req.site_domain,
        target_url=req.target_url,
        anchor_text=req.anchor_text,
        post_id=req.post_id,
        post_url=req.post_url
    )
    log_activity(req.site_domain, "backlink_added", {"target_url": req.target_url, "anchor_text": req.anchor_text})
    return {"success": True, "id": bid, "message": "Đã lưu backlink thành công"}

@router.post("/verify")
def verify_backlinks(current_user: dict = Depends(get_current_user)):
    backlinks = get_all_backlinks()
    verified_count = 0
    lost_count = 0
    with get_db() as conn:
        for b in backlinks:
            purl = b.get("post_url")
            if not purl:
                continue
            try:
                r = requests.get(purl, timeout=5, headers={"User-Agent": "PBN-Backlink-Checker/2.0"})
                if b["target_url"] in r.text:
                    conn.execute("UPDATE backlinks SET status = 'ACTIVE', last_verified = datetime('now','localtime') WHERE id = ?", (b["id"],))
                    verified_count += 1
                else:
                    conn.execute("UPDATE backlinks SET status = 'LOST', last_verified = datetime('now','localtime') WHERE id = ?", (b["id"],))
                    lost_count += 1
            except Exception:
                conn.execute("UPDATE backlinks SET status = 'ERROR', last_verified = datetime('now','localtime') WHERE id = ?", (b["id"],))
        conn.commit()
    return {"success": True, "verified": verified_count, "lost": lost_count}

@router.delete("/{backlink_id}")
def remove_backlink(backlink_id: int, current_user: dict = Depends(get_current_user)):
    delete_backlink(backlink_id)
    return {"success": True, "message": "Đã xóa backlink thành công"}

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from ..auth import get_current_user
from ..database import log_activity
from ..wp_user_runner import bulk_upsert_wp_users

router = APIRouter(prefix="/api/users", tags=["wp-users"])

class BulkWpUsersRequest(BaseModel):
    domains: List[str]
    username: str
    password: str
    email: Optional[str] = None
    role: str = "administrator"
    action: Optional[str] = "updateu"

@router.post("/bulk-wp-users")
def bulk_wp_users_endpoint(req: BulkWpUsersRequest, current_user: dict = Depends(get_current_user)):
    if not req.domains or len(req.domains) == 0:
        raise HTTPException(status_code=400, detail="Vui lòng cung cấp danh sách ít nhất 1 domain")
    
    if not req.username or not req.username.strip():
        raise HTTPException(status_code=400, detail="Username không được để trống")

    if not req.password or len(req.password.strip()) < 4:
        raise HTTPException(status_code=400, detail="Mật khẩu phải có ít nhất 4 ký tự")

    clean_role = req.role if req.role in ["administrator", "editor", "author", "contributor", "subscriber"] else "administrator"
    clean_action = req.action if req.action in ["createu", "updateu"] else "updateu"

    res = bulk_upsert_wp_users(
        domains=req.domains,
        username=req.username.strip(),
        password=req.password.strip(),
        email_template=req.email.strip() if req.email else None,
        role=clean_role,
        action=clean_action
    )

    log_activity(
        "system",
        "bulk_wp_users",
        {
            "user": current_user["username"],
            "total_domains": len(req.domains),
            "success": res.get("success_count", 0),
            "errors": res.get("error_count", 0),
            "target_user": req.username.strip(),
            "role": clean_role,
            "action": clean_action
        }
    )

    return res

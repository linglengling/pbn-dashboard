import time
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from ..auth import get_current_user
from ..database import log_activity
from ..cloudflare_service import (
    get_cf_accounts, save_cf_accounts, test_cf_credential, resolve_domain_via_cf
)

router = APIRouter(prefix="/api/cloudflare", tags=["cloudflare"])

class CFAccountItem(BaseModel):
    id: Optional[str] = None
    name: str
    token: Optional[str] = None
    email: Optional[str] = None
    key: Optional[str] = None

class CFSaveAccountsRequest(BaseModel):
    accounts: List[CFAccountItem]

class CFTestRequest(BaseModel):
    token: Optional[str] = None
    email: Optional[str] = None
    key: Optional[str] = None

@router.get("/accounts")
def list_cf_accounts(current_user: dict = Depends(get_current_user)):
    accounts = get_cf_accounts()
    # Mask secret tokens before sending to client for security
    masked = []
    for a in accounts:
        item = dict(a)
        if item.get("token"):
            t = item["token"]
            item["token_masked"] = t[:4] + "..." + t[-4:] if len(t) > 8 else "***"
        if item.get("key"):
            k = item["key"]
            item["key_masked"] = k[:4] + "..." + k[-4:] if len(k) > 8 else "***"
        masked.append(item)
    return {"success": True, "data": masked}

@router.post("/accounts")
def save_cf_accounts_endpoint(req: CFSaveAccountsRequest, current_user: dict = Depends(get_current_user)):
    existing = {a.get("id"): a for a in get_cf_accounts()}
    clean_accounts = []
    for idx, acc in enumerate(req.accounts):
        acc_dict = acc.dict()
        acc_id = acc_dict.get("id") or f"cf_{int(time.time())}_{idx}"
        acc_dict["id"] = acc_id

        old = existing.get(acc_id, {})
        # If token was masked or left blank, retain old token
        if not acc_dict.get("token") or "..." in str(acc_dict.get("token")):
            if old.get("token"):
                acc_dict["token"] = old["token"]
        # If key was masked or left blank, retain old key
        if not acc_dict.get("key") or "..." in str(acc_dict.get("key")):
            if old.get("key"):
                acc_dict["key"] = old["key"]

        clean_accounts.append(acc_dict)

    save_cf_accounts(clean_accounts)
    log_activity("system", "cloudflare_accounts_updated", {
        "user": current_user["username"],
        "count": len(clean_accounts)
    })
    return {"success": True, "message": f"Đã lưu {len(clean_accounts)} tài khoản Cloudflare thành công!"}

@router.post("/test")
def test_cf_endpoint(req: CFTestRequest, current_user: dict = Depends(get_current_user)):
    res = test_cf_credential(token=req.token, email=req.email, key=req.key)
    return res

@router.get("/resolve/{domain}")
def resolve_cf_domain(domain: str, current_user: dict = Depends(get_current_user)):
    res = resolve_domain_via_cf(domain)
    return {"success": True, "data": res}

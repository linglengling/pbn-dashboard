from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from ..database import get_settings, set_setting
from ..auth import get_current_user
from ..two_index_service import TwoIndexService

router = APIRouter(prefix="/api/indexing", tags=["indexing"])

class IndexingConfigRequest(BaseModel):
    api_key: str
    google: Optional[int] = 1
    bing: Optional[int] = 1
    yandex: Optional[int] = 0

class IndexingSubmitRequest(BaseModel):
    domains: List[str]
    mode: str = "homepage" # 'homepage', 'sitemap', 'custom_urls'
    custom_urls: Optional[List[str]] = None
    google: Optional[int] = 1
    bing: Optional[int] = 1
    yandex: Optional[int] = 0

class TestKeyRequest(BaseModel):
    api_key: str

class PreviewSitemapRequest(BaseModel):
    domain: str

@router.get("/status")
def get_indexing_status(current_user: dict = Depends(get_current_user)):
    st = get_settings()
    raw_key = st.get("TWO_INDEX_API_KEY", "").strip()
    has_key = bool(raw_key)
    
    masked_key = ""
    if has_key:
        if len(raw_key) > 8:
            masked_key = raw_key[:4] + "..." + raw_key[-4:]
        else:
            masked_key = "****"

    account_info = None
    if has_key:
        acc_res = TwoIndexService.get_account_info(raw_key)
        if acc_res.get("success"):
            account_info = acc_res.get("account")

    return {
        "success": True,
        "has_key": has_key,
        "masked_key": masked_key,
        "google": int(st.get("TWO_INDEX_GOOGLE", "1")),
        "bing": int(st.get("TWO_INDEX_BING", "1")),
        "yandex": int(st.get("TWO_INDEX_YANDEX", "0")),
        "account": account_info
    }

@router.post("/test-key")
def test_api_key(req: TestKeyRequest, current_user: dict = Depends(get_current_user)):
    key = req.api_key.strip()
    if not key:
        return {"success": False, "error": "Vui lòng nhập API Token"}
    
    res = TwoIndexService.get_account_info(key)
    return res

@router.post("/config")
def save_indexing_config(req: IndexingConfigRequest, current_user: dict = Depends(get_current_user)):
    key = req.api_key.strip()
    if not key:
        return {"success": False, "error": "Vui lòng nhập API Token"}

    # Test key first
    acc_res = TwoIndexService.get_account_info(key)
    if not acc_res.get("success"):
        return {
            "success": False,
            "error": f"Không thể xác thực API Token: {acc_res.get('error', 'Token không hợp lệ hoặc gói không hỗ trợ API')}"
        }

    set_setting("TWO_INDEX_API_KEY", key)
    set_setting("TWO_INDEX_GOOGLE", str(1 if req.google else 0))
    set_setting("TWO_INDEX_BING", str(1 if req.bing else 0))
    set_setting("TWO_INDEX_YANDEX", str(1 if req.yandex else 0))

    return {
        "success": True,
        "message": "Đã lưu và kết nối thành công API Key 2Index.ninja!",
        "account": acc_res.get("account")
    }

@router.post("/preview-sitemap")
def preview_sitemap(req: PreviewSitemapRequest, current_user: dict = Depends(get_current_user)):
    if not req.domain:
        return {"success": False, "error": "Vui lòng nhập tên miền"}
    
    res = TwoIndexService.discover_and_extract_sitemap(req.domain)
    return {
        "success": True,
        "data": res
    }

@router.post("/submit")
def submit_indexing(req: IndexingSubmitRequest, current_user: dict = Depends(get_current_user)):
    if not req.domains and not req.custom_urls:
        return {"success": False, "error": "Vui lòng chọn ít nhất 1 tên miền hoặc nhập URL"}

    res = TwoIndexService.submit_indexing_job(
        domains=req.domains,
        mode=req.mode,
        custom_urls=req.custom_urls,
        google=req.google,
        bing=req.bing,
        yandex=req.yandex
    )
    return res

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Any
from ..database import get_settings, set_setting, get_activity_logs
from ..auth import get_current_user

router = APIRouter(prefix="/api", tags=["settings"])

class SettingsUpdateRequest(BaseModel):
    settings: Dict[str, Any]

@router.get("/settings")
def list_settings(current_user: dict = Depends(get_current_user)):
    data = get_settings()
    return {"success": True, "data": data}

@router.post("/settings")
def update_settings(req: SettingsUpdateRequest, current_user: dict = Depends(get_current_user)):
    for k, v in req.settings.items():
        set_setting(k, str(v))
    return {"success": True, "message": "Đã lưu cài đặt thành công"}

@router.get("/log")
def list_logs(limit: int = 100, current_user: dict = Depends(get_current_user)):
    data = get_activity_logs(limit=limit)
    return {"success": True, "data": data}

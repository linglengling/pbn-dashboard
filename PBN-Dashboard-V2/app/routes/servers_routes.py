from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from ..database import (
    get_all_servers, get_server_by_id, create_server,
    update_server, delete_server, log_activity
)
from ..auth import get_current_user
from ..server_runner import (
    test_server, scan_server_sites, deploy_to_server, sync_scanned_sites
)

router = APIRouter(prefix="/api/servers", tags=["servers"])

class ServerCreateRequest(BaseModel):
    name: str
    type: str = "vps"
    host: str
    port: int = 22
    username: str
    password: str

class ServerUpdateRequest(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    status: Optional[str] = None

@router.get("")
def list_servers(current_user: dict = Depends(get_current_user)):
    data = get_all_servers()
    return {"success": True, "data": data}

@router.post("")
def add_server(req: ServerCreateRequest, current_user: dict = Depends(get_current_user)):
    srv_id = create_server(req.dict())
    log_activity(req.host, "server_created", {"name": req.name, "user": current_user["username"]})
    return {"success": True, "id": srv_id, "message": "Đã thêm máy chủ thành công"}

@router.put("/{server_id}")
def edit_server(server_id: int, req: ServerUpdateRequest, current_user: dict = Depends(get_current_user)):
    srv = get_server_by_id(server_id)
    if not srv:
        raise HTTPException(status_code=404, detail="Máy chủ không tồn tại")
    update_server(server_id, req.dict(exclude_unset=True))
    log_activity(srv["host"], "server_updated", {"id": server_id, "user": current_user["username"]})
    return {"success": True, "message": "Đã cập nhật máy chủ thành công"}

@router.delete("/{server_id}")
def remove_server(server_id: int, current_user: dict = Depends(get_current_user)):
    srv = get_server_by_id(server_id)
    if not srv:
        raise HTTPException(status_code=404, detail="Máy chủ không tồn tại")
    delete_server(server_id)
    log_activity(srv["host"], "server_deleted", {"id": server_id, "user": current_user["username"]})
    return {"success": True, "message": "Đã xóa máy chủ thành công"}

@router.post("/{server_id}/test")
def test_server_endpoint(server_id: int, current_user: dict = Depends(get_current_user)):
    srv = get_server_by_id(server_id)
    if not srv:
        raise HTTPException(status_code=404, detail="Máy chủ không tồn tại")
    res = test_server(srv)
    return res

@router.post("/{server_id}/scan")
def scan_server_endpoint(server_id: int, current_user: dict = Depends(get_current_user)):
    srv = get_server_by_id(server_id)
    if not srv:
        raise HTTPException(status_code=404, detail="Máy chủ không tồn tại")
    res = scan_server_sites(srv)
    if res.get("success"):
        synced_count = sync_scanned_sites(srv, res.get("sites", []))
        res["synced"] = synced_count
    return res

@router.post("/{server_id}/deploy")
def deploy_server_endpoint(server_id: int, current_user: dict = Depends(get_current_user)):
    srv = get_server_by_id(server_id)
    if not srv:
        raise HTTPException(status_code=404, detail="Máy chủ không tồn tại")
    res = deploy_to_server(srv)
    return res

@router.post("/scan-all")
def scan_all_endpoint(current_user: dict = Depends(get_current_user)):
    servers = get_all_servers()
    results = []
    total_found = 0
    total_synced = 0
    for s in servers:
        r = scan_server_sites(s)
        if r.get("success"):
            sites = r.get("sites", [])
            total_found += len(sites)
            synced = sync_scanned_sites(s, sites)
            total_synced += synced
            results.append({"server": s["name"], "host": s["host"], "success": True, "count": len(sites), "synced": synced})
        else:
            results.append({"server": s["name"], "host": s["host"], "success": False, "error": r.get("error")})
    return {"success": True, "total_found": total_found, "total_synced": total_synced, "details": results}

@router.post("/deploy-all")
def deploy_all_endpoint(current_user: dict = Depends(get_current_user)):
    servers = get_all_servers()
    results = []
    total_deployed = 0
    for s in servers:
        r = deploy_to_server(s)
        if r.get("success"):
            c = r.get("count", 0)
            total_deployed += c
            results.append({"server": s["name"], "host": s["host"], "success": True, "count": c})
        else:
            results.append({"server": s["name"], "host": s["host"], "success": False, "error": r.get("error")})
    return {"success": True, "total_deployed": total_deployed, "details": results}

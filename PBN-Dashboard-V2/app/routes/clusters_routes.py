from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import re

from ..database import get_clusters, create_or_get_cluster, delete_cluster, update_sites_cluster
from ..auth import get_current_user

router = APIRouter(prefix="/api/clusters", tags=["clusters"])

class CreateClusterRequest(BaseModel):
    name: str
    color: Optional[str] = "#38bdf8"
    description: Optional[str] = None

class AssignClusterRequest(BaseModel):
    domains: Optional[List[str]] = None
    site_domains: Optional[List[str]] = None
    domain: Optional[str] = None
    domain_text: Optional[str] = None
    cluster: str
    color: Optional[str] = None

@router.get("")
def list_clusters(current_user: dict = Depends(get_current_user)):
    return {"success": True, "data": get_clusters()}

@router.post("")
def create_cluster(req: CreateClusterRequest, current_user: dict = Depends(get_current_user)):
    name = req.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Tên cluster không được để trống")
    res = create_or_get_cluster(name, color=req.color, description=req.description)
    return {"success": True, "name": res, "message": f"Đã tạo cụm cluster '{res}' thành công"}

@router.delete("/{name}")
def remove_cluster(name: str, current_user: dict = Depends(get_current_user)):
    if name.lower() == "default":
        raise HTTPException(status_code=400, detail="Không thể xóa cụm mặc định (default)")
    delete_cluster(name)
    return {"success": True, "message": f"Đã xóa cụm cluster '{name}'"}

@router.post("/assign")
def assign_cluster(req: AssignClusterRequest, current_user: dict = Depends(get_current_user)):
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
        raise HTTPException(status_code=400, detail="Vui lòng cung cấp danh sách ít nhất 1 domain cần gán")

    cluster_name = req.cluster.strip()
    if not cluster_name:
        raise HTTPException(status_code=400, detail="Vui lòng chọn hoặc nhập tên cụm cluster")

    updated_count, clean_domains = update_sites_cluster(targets, cluster_name, color=req.color)
    return {
        "success": True,
        "cluster": cluster_name,
        "updated_count": updated_count,
        "total_requested": len(clean_domains),
        "message": f"Đã gán thành công {updated_count} website vào cụm cluster '{cluster_name}'!"
    }

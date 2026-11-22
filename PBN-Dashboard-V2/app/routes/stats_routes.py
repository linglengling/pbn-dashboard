from fastapi import APIRouter, Depends
from ..database import get_stats
from ..auth import get_current_user

router = APIRouter(prefix="/api", tags=["stats"])

@router.get("/stats")
def stats_endpoint(current_user: dict = Depends(get_current_user)):
    data = get_stats()
    return {"success": True, "data": data}

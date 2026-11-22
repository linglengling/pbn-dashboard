from fastapi import APIRouter, Depends
from ..database import get_all_posts
from ..auth import get_current_user

router = APIRouter(prefix="/api/posts", tags=["posts"])

@router.get("")
def list_posts(limit: int = 100, current_user: dict = Depends(get_current_user)):
    data = get_all_posts(limit=limit)
    return {"success": True, "data": data}

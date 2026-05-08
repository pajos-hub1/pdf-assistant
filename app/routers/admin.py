from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import validate_api_key, get_current_session, list_all_keys

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/keys")
async def admin_list_keys(
    db: Session = Depends(get_db),
    auth=Depends(get_current_session)
):
    return {"keys": list_all_keys(db)}
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db, register_user, login_user, get_all_chats
from app.database import Session as DBSession
from app.auth import validate_api_key

router = APIRouter(prefix="/auth", tags=["Auth"])


class RegisterRequest(BaseModel):
    owner_name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/register")
async def register(request: RegisterRequest):
    result = register_user(
        owner_name=request.owner_name,
        email=request.email,
        password=request.password
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {
        "message": "✅ Registration successful",
        "owner": result["owner"],
        "email": result["email"],
        "api_key": result["api_key"]
    }


@router.post("/login")
async def login(request: LoginRequest):
    from app.database import login_user
    result = login_user(email=request.email, password=request.password)
    if "error" in result:
        raise HTTPException(status_code=401, detail=result["error"])
    return {
        "message": "✅ Login successful",
        "owner": result["owner"],
        "email": result["email"],
        "api_key": result["api_key"]
    }


@router.get("/me")
async def get_me(
    db: Session = Depends(get_db),
    auth=Depends(validate_api_key)
):
    last_session = (
        db.query(DBSession)
        .filter(DBSession.api_key_id == auth.id)
        .order_by(DBSession.last_active.desc())
        .first()
    )
    chats = get_all_chats(db, api_key_id=auth.id)
    return {
        "owner": auth.owner_name,
        "email": auth.email,
        "session_id": last_session.id if last_session else None,
        "chats": chats
    }
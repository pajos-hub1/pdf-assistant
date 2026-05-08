from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db, register_user, login_user, get_all_chats
from app.database import Session as DBSession, APIKey
from app.auth import validate_token
from app.jwt_handler import create_token_pair, verify_refresh_token
from app.sanitizer import sanitize_name, sanitize_email, sanitize_password

router = APIRouter(prefix="/auth", tags=["Auth"])


class RegisterRequest(BaseModel):
    owner_name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/register")
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    # Sanitize inputs
    owner_name = sanitize_name(request.owner_name)
    email = sanitize_email(request.email)
    password = sanitize_password(request.password)

    result = register_user(
        owner_name=owner_name,
        email=email,
        password=password
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    # Get user ID for token
    user = db.query(APIKey).filter(APIKey.email == email).first()
    tokens = create_token_pair(user.id, email, owner_name)

    return {
        "message": "✅ Registration successful",
        "owner": result["owner"],
        "email": result["email"],
        **tokens
    }


@router.post("/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    # Sanitize email only — don't validate password format on login
    try:
        email = sanitize_email(request.email)
    except HTTPException:
        raise HTTPException(status_code=400, detail="❌ Invalid email address.")

    result = login_user(email=email, password=request.password)
    if "error" in result:
        raise HTTPException(status_code=401, detail=result["error"])

    user = db.query(APIKey).filter(APIKey.email == email).first()
    tokens = create_token_pair(user.id, email, result["owner"])

    return {
        "message": "✅ Login successful",
        "owner": result["owner"],
        "email": result["email"],
        **tokens
    }

@router.post("/refresh")
async def refresh_token(
    request: RefreshRequest,
    db: Session = Depends(get_db)
):
    """Use refresh token to get a new access token."""
    payload = verify_refresh_token(request.refresh_token)

    user_id = int(payload.get("sub"))
    user = db.query(APIKey).filter(APIKey.id == user_id).first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="❌ User not found or deactivated."
        )

    tokens = create_token_pair(user.id, user.email, user.owner_name)
    return {
        "message": "✅ Token refreshed",
        **tokens
    }


@router.get("/me")
async def get_me(
    db: Session = Depends(get_db),
    auth=Depends(validate_token)
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
from fastapi import Security, HTTPException, status, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db, APIKey, get_or_create_session
from app.jwt_handler import verify_access_token

# JWT Bearer scheme
bearer_scheme = HTTPBearer(auto_error=False)


# ─────────────────────────────────────────
# CORE JWT VALIDATION
# ─────────────────────────────────────────

def validate_token(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
    db: Session = Depends(get_db)
) -> APIKey:
    """
    Validates the JWT Bearer token.
    Raises 401 if missing, expired, or invalid.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="❌ Missing token. Add Authorization: Bearer <token> header.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Verify token and extract payload
    payload = verify_access_token(credentials.credentials)

    # Load user from DB
    user_id = int(payload.get("sub"))
    user = db.query(APIKey).filter(APIKey.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="❌ User not found."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="❌ Account deactivated."
        )

    return user


# Keep validate_api_key as alias for backward compatibility
validate_api_key = validate_token


def get_current_session(
    session_id: Optional[str] = Header(None, alias="X-Session-Id"),
    auth: APIKey = Depends(validate_token),
    db: Session = Depends(get_db)
):
    """Gets or creates a session for the current user."""
    session = get_or_create_session(
        db,
        api_key_id=auth.id,
        session_id=session_id
    )
    return {
        "session": session,
        "owner": auth.owner_name,
        "api_key_id": auth.id
    }


# ─────────────────────────────────────────
# ADMIN HELPERS
# ─────────────────────────────────────────

def deactivate_key(db: Session, key: str) -> bool:
    db_key = db.query(APIKey).filter(APIKey.key == key).first()
    if db_key:
        db_key.is_active = False
        db.commit()
        return True
    return False


def reactivate_key(db: Session, key: str) -> bool:
    db_key = db.query(APIKey).filter(APIKey.key == key).first()
    if db_key:
        db_key.is_active = True
        db.commit()
        return True
    return False


def list_all_keys(db: Session) -> list:
    keys = db.query(APIKey).all()
    return [
        {
            "id": k.id,
            "owner": k.owner_name,
            "email": k.email,
            "is_active": k.is_active,
            "created_at": k.created_at
        }
        for k in keys
    ]
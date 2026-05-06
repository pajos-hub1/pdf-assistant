from fastapi import Security, HTTPException, status, Depends, Header
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from app.database import get_db, APIKey, get_or_create_session
from typing import Optional

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def validate_api_key(
    api_key: str = Security(API_KEY_HEADER),
    db: Session = Depends(get_db)
) -> APIKey:
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="❌ Missing API key. Add X-API-Key header to your request.",
            headers={"WWW-Authenticate": "API-Key"}
        )

    db_key = db.query(APIKey).filter(APIKey.key == api_key).first()

    if not db_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="❌ Invalid API key.",
            headers={"WWW-Authenticate": "API-Key"}
        )

    if not db_key.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="❌ This API key has been deactivated. Contact the administrator."
        )

    return db_key


def get_current_session(
    # Read session_id from header — optional, creates new if not provided
    session_id: Optional[str] = Header(None, alias="X-Session-Id"),
    api_key: APIKey = Depends(validate_api_key),
    db: Session = Depends(get_db)
):
    """
    Gets or creates a session for the current user.
    Session ID comes from X-Session-Id header.
    If not provided, a new session is created automatically.
    """
    session = get_or_create_session(
        db,
        api_key_id=api_key.id,
        session_id=session_id
    )
    return {
        "session": session,
        "owner": api_key.owner_name,
        "api_key_id": api_key.id
    }


# ─────────────────────────────────────────
# ADMIN HELPERS
# ─────────────────────────────────────────

def deactivate_key(db: Session, key: str) -> bool:
    """Deactivate an API key — user loses access immediately."""
    db_key = db.query(APIKey).filter(APIKey.key == key).first()
    if db_key:
        db_key.is_active = False
        db.commit()
        print(f"🔒 API key deactivated: {key}")
        return True
    return False


def reactivate_key(db: Session, key: str) -> bool:
    """Reactivate a previously deactivated API key."""
    db_key = db.query(APIKey).filter(APIKey.key == key).first()
    if db_key:
        db_key.is_active = True
        db.commit()
        print(f"🔓 API key reactivated: {key}")
        return True
    return False


def list_all_keys(db: Session) -> list:
    """List all API keys — for admin use."""
    keys = db.query(APIKey).all()
    return [
        {
            "id": k.id,
            "owner": k.owner_name,
            "key": k.key,
            "is_active": k.is_active,
            "created_at": k.created_at
        }
        for k in keys
    ]
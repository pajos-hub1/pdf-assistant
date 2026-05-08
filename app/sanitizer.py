import bleach
import re
from fastapi import HTTPException


# ─────────────────────────────────────────
# TEXT SANITIZATION
# ─────────────────────────────────────────

def sanitize_text(text: str, max_length: int = 2000) -> str:
    """
    Clean user input — strip HTML, limit length,
    remove null bytes and control characters.
    """
    if not text:
        return ""

    # Strip HTML tags completely
    text = bleach.clean(text, tags=[], strip=True)

    # Remove null bytes
    text = text.replace("\x00", "")

    # Remove other control characters except newlines and tabs
    text = re.sub(r'[\x01-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

    # Trim whitespace
    text = text.strip()

    # Enforce max length
    if len(text) > max_length:
        raise HTTPException(
            status_code=400,
            detail=f"❌ Input too long. Maximum {max_length} characters allowed."
        )

    return text


def sanitize_name(name: str, max_length: int = 100) -> str:
    """Sanitize a name field — alphanumeric + spaces + basic punctuation."""
    if not name:
        return ""

    name = bleach.clean(name, tags=[], strip=True)
    name = name.replace("\x00", "")
    name = name.strip()

    if len(name) > max_length:
        raise HTTPException(
            status_code=400,
            detail=f"❌ Name too long. Maximum {max_length} characters."
        )

    if not name:
        raise HTTPException(
            status_code=400,
            detail="❌ Name cannot be empty."
        )

    return name


def sanitize_email(email: str) -> str:
    """Validate and sanitize email address."""
    if not email:
        raise HTTPException(status_code=400, detail="❌ Email is required.")

    email = email.strip().lower()

    # Basic email regex
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise HTTPException(
            status_code=400,
            detail="❌ Invalid email address."
        )

    if len(email) > 255:
        raise HTTPException(
            status_code=400,
            detail="❌ Email too long."
        )

    return email


def sanitize_password(password: str) -> str:
    """Validate password strength."""
    if not password:
        raise HTTPException(
            status_code=400,
            detail="❌ Password is required."
        )

    if len(password) < 8:
        raise HTTPException(
            status_code=400,
            detail="❌ Password must be at least 8 characters."
        )

    if len(password) > 128:
        raise HTTPException(
            status_code=400,
            detail="❌ Password too long."
        )

    if not re.search(r'[A-Z]', password):
        raise HTTPException(
            status_code=400,
            detail="❌ Password must contain at least one uppercase letter."
        )

    if not re.search(r'[a-z]', password):
        raise HTTPException(
            status_code=400,
            detail="❌ Password must contain at least one lowercase letter."
        )

    if not re.search(r'[0-9]', password):
        raise HTTPException(
            status_code=400,
            detail="❌ Password must contain at least one number."
        )

    if not re.search(r'[^A-Za-z0-9]', password):
        raise HTTPException(
            status_code=400,
            detail="❌ Password must contain at least one special character."
        )

    return password
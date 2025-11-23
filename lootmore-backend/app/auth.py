import os, hashlib
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from .models import User

SALT = os.getenv("LOOTMORE_TOKEN_SALT", "dev-salt-change-me")

def hash_token(token: str) -> str:
    token = token.strip()
    return hashlib.sha256((token + SALT).encode("utf-8")).hexdigest()

def auth_user(db: Session, raw_token: str) -> User | None:
    if not raw_token:
        return None
    th = hash_token(raw_token)
    user = db.query(User).filter(User.token_hash == th).first()
    if not user:
        return None
    if not user.is_active or user.tier == "banned":
        return None
    return user

def ensure_quota(user: User):
    """Resets quota daily and checks remaining."""
    now = datetime.now(timezone.utc)

    if user.quota_reset_at is None or now >= user.quota_reset_at:
        # reset at next UTC midnight
        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        user.used_today = 0
        user.quota_reset_at = tomorrow

    if user.used_today >= user.daily_quota:
        return False
    return True

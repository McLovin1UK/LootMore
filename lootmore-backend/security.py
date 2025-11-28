import hashlib
import os

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import ApiToken, reset_quota_if_needed


def hash_token(raw_token: str, salt: str) -> str:
    return hashlib.sha256((salt + raw_token).encode()).hexdigest()


def verify_token(raw_token: str, db: Session):
    salt = os.getenv("LOOTMORE_TOKEN_SALT")
    if not salt:
        raise HTTPException(status_code=500, detail="Server token salt not configured")

    token_hash = hash_token(raw_token, salt)
    token = db.query(ApiToken).filter(ApiToken.token_hash == token_hash).first()
    if not token:
        return None

    reset_quota_if_needed(token)

    if token.used_today >= token.daily_quota:
        raise HTTPException(status_code=429, detail="Daily quota exceeded")

    token.used_today += 1
    db.commit()
    return token

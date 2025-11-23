from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from .db import get_db
from .models import User
from .auth import hash_token
from .schemas import AdminBanRequest, AdminRotateRequest
import secrets

router = APIRouter(prefix="/admin")

def require_admin(authorization: str | None):
    # ultra-simple admin gate:
    # set ADMIN_TOKEN in env, call with Bearer ADMIN_TOKEN
    import os
    admin_tok = os.getenv("ADMIN_TOKEN")
    if not admin_tok:
        raise HTTPException(500, "ADMIN_TOKEN not set")
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Admin auth required")
    if authorization.split(" ",1)[1].strip() != admin_tok:
        raise HTTPException(403, "Forbidden")

@router.post("/ban")
def ban_user(
    req: AdminBanRequest,
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None)
):
    require_admin(authorization)
    th = hash_token(req.token)
    user = db.query(User).filter(User.token_hash == th).first()
    if not user:
        raise HTTPException(404, "User not found")

    user.is_active = False
    user.tier = "banned"
    db.add(user)
    db.commit()
    return {"ok": True, "user_id": str(user.id)}

@router.post("/rotate")
def rotate_token(
    req: AdminRotateRequest,
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None)
):
    require_admin(authorization)
    th = hash_token(req.token)
    user = db.query(User).filter(User.token_hash == th).first()
    if not user:
        raise HTTPException(404, "User not found")

    new_token = "lm_alpha_" + secrets.token_urlsafe(12)
    user.token_hash = hash_token(new_token)
    db.add(user)
    db.commit()

    return {"ok": True, "user_id": str(user.id), "new_token": new_token}

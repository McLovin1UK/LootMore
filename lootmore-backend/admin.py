import os
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from manage_tokens import create_token_entry, revoke_token, update_quota
from models import ApiToken, ApiUsageLog

router = APIRouter()
templates = Jinja2Templates(directory="templates")


class CreateTokenRequest(BaseModel):
    daily_quota: int | None = None


class TokenIdRequest(BaseModel):
    id: int


class UpdateTokenRequest(BaseModel):
    id: int
    daily_quota: int


class LoginRequest(BaseModel):
    password: str


def require_admin(request: Request, x_admin_key: str | None = Header(default=None)) -> None:
    admin_password = os.getenv("LOOTMORE_ADMIN_PASSWORD")
    if not admin_password:
        raise HTTPException(status_code=500, detail="Admin password not configured")
    provided_key = x_admin_key or request.cookies.get("admin_key")
    if provided_key != admin_password:
        raise HTTPException(status_code=401, detail="Unauthorized")


def _format_token(token: ApiToken) -> dict[str, Any]:
    return {
        "id": token.id,
        "daily_quota": token.daily_quota,
        "used_today": token.used_today,
        "last_reset_at": token.last_reset_at.isoformat() if token.last_reset_at else None,
    }


def _get_recent_logs(db: Session, limit: int = 20) -> list[ApiUsageLog]:
    return (
        db.query(ApiUsageLog)
        .order_by(ApiUsageLog.timestamp.desc())
        .limit(limit)
        .all()
    )


def _get_stats(db: Session) -> dict[str, Any]:
    total_tokens = db.query(func.count(ApiToken.id)).scalar() or 0
    total_requests = db.query(func.count(ApiUsageLog.id)).scalar() or 0
    successful_requests = (
        db.query(func.count(ApiUsageLog.id)).filter(ApiUsageLog.success.is_(True)).scalar() or 0
    )
    success_rate = None
    if total_requests:
        success_rate = round((successful_requests / total_requests) * 100, 2)

    return {
        "total_tokens": total_tokens,
        "total_requests": total_requests,
        "success_rate": success_rate,
    }


@router.get("/", include_in_schema=False)
async def admin_root(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request})


@router.get("/dashboard")
async def admin_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    stats = _get_stats(db)
    logs = _get_recent_logs(db)
    return templates.TemplateResponse(
        "admin_index.html",
        {"request": request, "stats": stats, "logs": logs},
    )


@router.get("/tokens")
async def list_tokens(
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    tokens = db.query(ApiToken).all()
    token_payloads = [_format_token(token) for token in tokens]

    if "text/html" in request.headers.get("accept", ""):
        return templates.TemplateResponse(
            "admin_tokens.html",
            {"request": request, "tokens": tokens},
        )

    return token_payloads


@router.post("/tokens/create")
async def create_token(
    payload: CreateTokenRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    _, raw_token = create_token_entry(db, payload.daily_quota)
    return {"token": raw_token}


@router.post("/tokens/revoke")
async def revoke_token_api(
    payload: TokenIdRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    if not revoke_token(db, payload.id):
        raise HTTPException(status_code=404, detail="Token not found")
    return {"status": "revoked"}


@router.post("/tokens/update")
async def update_token(
    payload: UpdateTokenRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    if not update_quota(db, payload.id, payload.daily_quota):
        raise HTTPException(status_code=404, detail="Token not found")
    return {"status": "updated"}


@router.get("/logs")
async def list_logs(
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    logs = _get_recent_logs(db, limit=100)
    if "text/html" in request.headers.get("accept", ""):
        return templates.TemplateResponse(
            "admin_logs.html",
            {"request": request, "logs": logs},
        )

    return [
        {
            "id": log.id,
            "token_id": log.token_id,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "request_ip": log.request_ip,
            "latency_ms": log.latency_ms,
            "text_length": log.text_length,
            "success": log.success,
        }
        for log in logs
    ]


@router.post("/login")
async def admin_login(payload: LoginRequest):
    admin_password = os.getenv("LOOTMORE_ADMIN_PASSWORD")
    if not admin_password or payload.password != admin_password:
        raise HTTPException(status_code=401, detail="Unauthorized")

    response = JSONResponse({"status": "ok"})
    response.set_cookie("admin_key", payload.password, httponly=True, samesite="lax")
    return response

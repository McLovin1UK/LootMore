import time
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from .db import get_db
from .schemas import CalloutRequest, CalloutResponse
from .models import UsageEvent
from .auth import auth_user, ensure_quota

# TODO: replace with your actual OpenAI server-side call
def generate_callout_and_audio(image_b64: str, game: str):
    # placeholder for now
    text = "Backend wired. Replace generate_callout_and_audio with real OpenAI call."
    audio_b64 = None
    return text, audio_b64, None

router = APIRouter()

@router.post("/callout", response_model=CalloutResponse)
def callout(
    payload: CalloutRequest,
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None)
):
    start = time.time()

    raw_token = None
    if authorization and authorization.lower().startswith("bearer "):
        raw_token = authorization.split(" ", 1)[1].strip()

    user = auth_user(db, raw_token)

    if not user:
        db.add(UsageEvent(
            user_id=None,
            game=payload.game,
            client_version=payload.client_version,
            status="unauthorized",
            error_code="401",
            error_msg="Invalid or inactive token"
        ))
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid token")

    if not ensure_quota(user):
        db.add(UsageEvent(
            user_id=user.id,
            game=payload.game,
            client_version=payload.client_version,
            status="over_quota",
            error_code="429",
            error_msg="Daily quota exceeded"
        ))
        db.commit()
        raise HTTPException(status_code=429, detail="Daily quota exceeded")

    # Generate callout
    try:
        text, audio_b64, audio_url = generate_callout_and_audio(payload.image_b64, payload.game)
        latency_ms = int((time.time() - start) * 1000)

        user.used_today += 1
        user.last_seen_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
        db.add(user)

        db.add(UsageEvent(
            user_id=user.id,
            game=payload.game,
            client_version=payload.client_version,
            status="ok",
            latency_ms=latency_ms,
            callout_text=text
        ))
        db.commit()

        return CalloutResponse(text=text, audio_b64=audio_b64, audio_url=audio_url)

    except Exception as e:
        latency_ms = int((time.time() - start) * 1000)
        db.add(UsageEvent(
            user_id=user.id,
            game=payload.game,
            client_version=payload.client_version,
            status="error",
            latency_ms=latency_ms,
            error_code="500",
            error_msg=str(e)
        ))
        db.commit()
        raise HTTPException(status_code=500, detail="Backend error")
